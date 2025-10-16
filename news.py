import os, time, requests
from .config import settings
from .alert_router import AlertRouter

NEWS_SOURCES = [
    ("newsapi", "https://newsapi.org/v2/everything"),  # needs NEWSAPI_KEY
]

KEYWORDS = ["bitcoin", "btc", "ethereum", "eth", "crypto", "sec", "etf", "binance", "coinbase", "regulation"]
SEEN = set()

def fetch_news_newsapi():
    if not settings.newsapi_key:
        return []
    url = "https://newsapi.org/v2/everything"
    q = " OR ".join(KEYWORDS)
    params = {
        "q": q,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 20,
        "apiKey": settings.newsapi_key
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    out = []
    for a in data.get("articles", []):
        uid = a.get("url")
        if uid in SEEN:
            continue
        SEEN.add(uid)
        out.append({
            "title": a.get("title"),
            "url": a.get("url"),
            "source": a.get("source", {}).get("name", ""),
        })
    return out

def run_news_cycle(router: AlertRouter):
    items = []
    items += fetch_news_newsapi()
    # TODO: add CryptoNews API / other sources similarly

    for it in items:
        title = f"{it['source']} — {it['title']}" if it['source'] else it['title']
        body = it['url']
        router.bot and router.bot.loop.create_task(router.send("Crypto News", f"{title}\n{body}", key=it['url']))
