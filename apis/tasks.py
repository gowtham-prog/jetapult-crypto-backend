import os
import time
import logging
import requests
from datetime import date
from decimal import Decimal
from celery import shared_task
from django.db import transaction
from .models import Coin, HistoricalPrice

COINGECKO_API_KEY = os.getenv("COINGECKO_APIKEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

logger = logging.getLogger(__name__)


def _headers():
    headers = {"accept": "application/json"}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY
    return headers


@shared_task(bind=True, max_retries=3)
def fetch_top_coins(self, n=10):
    """
    Fetch top N coins from CoinGecko and save to DB.
    """
    url = f"{COINGECKO_BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": n,
        "page": 1,
        "sparkline": "false"
    }

    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"HTTPError fetching top coins: {resp.status_code} {resp.text}")
        raise self.retry(exc=e, countdown=10)
    except requests.RequestException as e:
        logger.error(f"RequestException fetching top coins: {e}")
        raise self.retry(exc=e, countdown=10)

    data = resp.json()
    logger.info(f"Retrieved {len(data)} coins from CoinGecko.")

    with transaction.atomic():
        for coin_data in data:
            Coin.objects.update_or_create(
                coingecko_id=coin_data["id"],
                defaults={
                    "symbol": coin_data["symbol"],
                    "name": coin_data["name"],
                    "market_cap_rank": coin_data.get("market_cap_rank"),
                    "last_price": coin_data["current_price"],
                    "volume": coin_data["total_volume"],
                    "percent_change_24h": coin_data.get("price_change_percentage_24h"),
                },
            )


@shared_task(bind=True, max_retries=3)
def fetch_coin_history(self, coingecko_id, days=30, sleep_interval=1.5):
    """
    Fetch historical prices for a coin for the last X days and store them.
    Adds a delay between API calls to avoid 429 errors.
    """
    url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}

    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"HTTPError fetching history for {coingecko_id}: {resp.status_code} {resp.text}")
        raise self.retry(exc=e, countdown=10)
    except requests.RequestException as e:
        logger.error(f"RequestException fetching history for {coingecko_id}: {e}")
        raise self.retry(exc=e, countdown=10)

    data = resp.json()
    prices = data.get("prices", [])

    try:
        coin = Coin.objects.get(coingecko_id=coingecko_id)
    except Coin.DoesNotExist:
        logger.error(f"Coin {coingecko_id} does not exist in DB.")
        return

    with transaction.atomic():
        for timestamp, price in prices:
            dt = date.fromtimestamp(timestamp / 1000.0)
            HistoricalPrice.objects.update_or_create(
                coin=coin,
                date=dt,
                defaults={"price": Decimal(str(price))},
            )
            # sleep to avoid hitting rate limits
            time.sleep(sleep_interval)

    logger.info(f"Saved {len(prices)} historical prices for {coingecko_id}.")
