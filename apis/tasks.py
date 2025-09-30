import os
import time
import logging
import requests
from datetime import date, datetime
from decimal import Decimal
from celery import shared_task
from django.db import transaction
from .models import Coin, HistoricalPrice
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

COINGECKO_API_KEY = os.getenv("COINGECKO_APIKEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


def _headers():
    headers = {"accept": "application/json"}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY
    return headers


@shared_task(bind=True, max_retries=3)
def fetch_top_coins(self, n=10):
    """
    Fetch top N coins by market cap and store/update them in DB.
    """
    url = f"{COINGECKO_BASE_URL}/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": n, "page": 1}
    flag = False
    
    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"HTTPError fetching top coins: {resp.status_code} {resp.text}")
        if resp.status_code >= 500 or resp.status_code == 429:
            raise self.retry(exc=e, countdown=10)
        return
    except requests.RequestException as e:
        logger.error(f"RequestException fetching top coins: {e}")
        raise self.retry(exc=e, countdown=10)
    
    data = resp.json()

    if Coin.objects.count() == 0:
        flag = True

    with transaction.atomic():
        for c in data:
            Coin.objects.update_or_create(
                coingecko_id=c["id"],
                defaults={
                    "symbol": c["symbol"].upper(),
                    "name": c["name"],
                    "market_cap_rank": c.get("market_cap_rank"),
                    "last_price": Decimal(str(c["current_price"])),
                    "volume": Decimal(str(c["total_volume"])),
                    "percent_change_24h": c.get("price_change_percentage_24h"),
                },
            )
    
    if flag:
        fetch_all_coins_history.delay(days=30, sleep_between_coins=30)
    logger.info(f"Successfully fetched and stored {len(data)} top coins.")


@shared_task(bind=True, max_retries=3)
def fetch_all_coins_history(self, days=30, sleep_between_coins=30):
    """
    Enqueue or fetch historical prices for all coins in the database.

    Args:
        days: Number of days of historical data to fetch per coin
        sleep_between_coins: Optional delay between scheduling each coin
    """
    coin_ids = list(Coin.objects.values_list("coingecko_id", flat=True))
    if not coin_ids:
        logger.info("No coins found to fetch history for.")
        return

    logger.info(f"Scheduling history fetch for {len(coin_ids)} coins (days={days}).")
    for coingecko_id in coin_ids:
        try:
            fetch_coin_history.delay(coingecko_id, days=days)
        except Exception as e:
            logger.error(f"Failed to schedule history for {coingecko_id}: {e}")
        if sleep_between_coins > 0:
            time.sleep(sleep_between_coins)

@shared_task(bind=True, max_retries=3)
def fetch_coin_history(self, coingecko_id, days=30, sleep_interval=0.1):
    """
    Fetch historical prices for a coin from Coingecko API and store them.
    Includes retry logic and rate-limiting delays.
    
    Args:
        coingecko_id: The CoinGecko ID of the coin
        days: Number of days of historical data to fetch
        sleep_interval: Delay between processing each price point (in seconds)
    """
    url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}/market_chart"
    logger.info(f"Fetching history for { url} days")
    params = {"vs_currency": "usd", "days": days}

    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"HTTPError fetching history for {coingecko_id}: {resp.status_code} {resp.text}")
        if resp.status_code >= 500 or resp.status_code == 429:
            raise self.retry(exc=e, countdown=30)
        return
    except requests.RequestException as e:
        logger.error(f"RequestException fetching history for {coingecko_id}: {e}")
        raise self.retry(exc=e, countdown=10)

    data = resp.json()
    prices = data.get("prices", [])

    if not prices:
        logger.warning(f"No price data returned for {coingecko_id}.")
        return

    try:
        coin = Coin.objects.get(coingecko_id=coingecko_id)
    except Coin.DoesNotExist:
        logger.error(f"Coin {coingecko_id} does not exist in DB.")
        return

    with transaction.atomic():
        for timestamp, price in prices:
            dt = datetime.fromtimestamp(timestamp / 1000.0).date()
            HistoricalPrice.objects.update_or_create(
                coin=coin,
                date=dt,
                defaults={"price": Decimal(str(price))},
            )
        # Sleep outside the loop to avoid excessive delays
        if sleep_interval > 0:
            time.sleep(sleep_interval)

    logger.info(f"Saved {len(prices)} historical prices for {coingecko_id}.")
