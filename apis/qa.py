import re
from datetime import date, timedelta
from .models import Coin

# Precompiled regex for efficiency
PRICE_RE = re.compile(r"(?:price|worth|how much).*?(?P<coin>\w+)", re.I)
TREND_RE = re.compile(r"(?:(?P<days>\d+)\s*(?:day|d)\s*(?:trend|chart)|last\s(?P<days2>\d+)\s*days)", re.I)

def resolve_coin(text: str):
    """Try to resolve a coin by matching name or symbol in user text."""
    text = text.lower()
    for coin in Coin.objects.all():
        if coin.name.lower() in text or coin.symbol.lower() in text:
            return coin
    return None

def handle_query(text: str):
    """Process a user query and return structured response for chat assistant panel."""
    text = text.lower().strip()

    # --- PRICE QUERIES ---
    if PRICE_RE.search(text):
        coin = resolve_coin(text)
        if coin:
            return {
                "type": "price",
                "coin": coin.coingecko_id,
                "answer": f"The current price of {coin.name} is ${coin.last_price:.2f}",
                "data": {"price": float(coin.last_price)}
            }
        return {"type": "unknown", "answer": "❌ I couldn't find that coin. Please check the name or symbol."}

    # --- TREND QUERIES ---
    trend_match = TREND_RE.search(text)
    if trend_match:
        days = trend_match.group("days") or trend_match.group("days2")
        days = int(days) if days else 7
        coin = resolve_coin(text)
        if coin:
            start_date = date.today() - timedelta(days=days)
            history = (
                coin.history
                .filter(date__gte=start_date)
                .order_by("date")
                .values("date", "price")
            )
            return {
                "type": "trend",
                "coin": coin.coingecko_id,
                "answer": f"📈 Showing {days}-day trend for {coin.name}",
                "data": list(history)
            }
        return {"type": "unknown", "answer": "❌ Coin not found for trend query."}

    # --- HELP / DEFAULT ---
    return {
        "type": "help",
        "answer": (
            "💡 I can answer crypto price & trend queries.\n\n"
            "Try:\n"
            "- 'price of bitcoin'\n"
            "- 'how much is ETH worth?'\n"
            "- '7-day trend of solana'"
        )
    }
