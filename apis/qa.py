import re
from datetime import date, timedelta
from .models import Coin

PRICE_RE = re.compile(r"(price|worth|how much).*(?P<coin>\w+)", re.I)
TREND_RE = re.compile(r"(?P<days>\d+)\s*(?:day|d)\s*(trend|chart)|last\s(?P<days2>\d+)\sdays", re.I)

def resolve_coin(text):
    text = text.lower()
    for coin in Coin.objects.all():
        if coin.name.lower() in text or coin.symbol.lower() in text:
            return coin
    return None

def handle_query(text):
    text = text.lower()

    # Price queries
    if "price" in text or "worth" in text or "how much" in text:
        coin = resolve_coin(text)
        if coin:
            return {
                "type": "price",
                "coin": coin.coingecko_id,
                "answer": f"{coin.name} price is ${coin.last_price}",
                "data": {"price": float(coin.last_price)}
            }
        return {"type": "unknown", "answer": "Sorry, I couldn't find that coin."}

    # Trend queries
    m = TREND_RE.search(text)
    if m:
        days = m.group("days") or m.group("days2")
        days = int(days) if days else 7
        coin = resolve_coin(text)
        if coin:
            start_date = date.today() - timedelta(days=days)
            history = coin.history.filter(date__gte=start_date).order_by("date").values("date", "price")
            return {
                "type": "trend",
                "coin": coin.coingecko_id,
                "answer": f"Showing {days}-day trend for {coin.name}",
                "data": list(history)
            }
        return {"type": "unknown", "answer": "Coin not found for trend query."}

    return {"type": "help", "answer": "I can answer price and trend queries. Try 'price of bitcoin' or '7-day trend of eth'."}
