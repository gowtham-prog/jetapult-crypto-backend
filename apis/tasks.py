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

    with transaction.atomic():
        for c in data:
            coin, _ = Coin.objects.update_or_create(
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
            # fetch historical data for each coin
            fetch_coin_history.delay(coin.coingecko_id, days=30)
    
    logger.info(f"Successfully fetched and stored {len(data)} top coins.")


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
        # Only retry if it's a server error or rate limit; 400 errors are usually invalid request
        if resp.status_code >= 500 or resp.status_code == 429:
            raise self.retry(exc=e, countdown=10)
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
