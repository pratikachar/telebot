import httpx
import feedparser
from urllib.parse import quote

from config import TMDB_API_KEY

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

TOPICS = {
    "world": "WORLD",
    "india": "INDIA",
    "business": "BUSINESS",
    "technology": "TECHNOLOGY",
    "sports": "SPORTS",
    "entertainment": "ENTERTAINMENT",
    "science": "SCIENCE",
    "health": "HEALTH",
}

LANGS = {
    "en": ("en-IN", "en"),
    "hi": ("hi-IN", "hi"),
    "ta": ("ta-IN", "ta"),
    "te": ("te-IN", "te"),
    "bn": ("bn-IN", "bn"),
    "mr": ("mr-IN", "mr"),
    "gu": ("gu-IN", "gu"),
    "kn": ("kn-IN", "kn"),
    "ml": ("ml-IN", "ml"),
    "pa": ("pa-IN", "pa"),
}

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Light showers",
    81: "Showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm",
}


async def _get_json(url, params=None, headers=None):
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def get_news(category=None, lang="en"):
    hl, ceid = LANGS.get(lang, LANGS["en"])
    if category:
        cat = category.lower().strip()
        if cat in TOPICS:
            url = (
                f"https://news.google.com/rss/headlines/section/topic/{TOPICS[cat]}"
                f"?hl={hl}&gl=IN&ceid=IN:{ceid}"
            )
        elif cat in LANGS:
            hl, ceid = LANGS[cat]
            url = f"https://news.google.com/rss?hl={hl}&gl=IN&ceid=IN:{ceid}"
        else:
            url = (
                f"https://news.google.com/rss/search?q={quote(cat)}"
                f"&hl={hl}&gl=IN&ceid=IN:{ceid}"
            )
    else:
        url = f"https://news.google.com/rss?hl={hl}&gl=IN&ceid=IN:{ceid}"

    async with httpx.AsyncClient(timeout=20, headers=UA) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    items = []
    for entry in feed.entries[:6]:
        items.append((entry.get("title", ""), entry.get("link", "")))
    if not items:
        return "No news found. Try a different category or language."
    return items


async def get_weather(city):
    geo = await _get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = geo.get("results")
    if not results:
        return f"City '{city}' not found. Try /weather Mumbai"
    place = results[0]
    lat = place["latitude"]
    lon = place["longitude"]
    name = place.get("name", city)
    region = place.get("admin1") or place.get("country")
    fc = await _get_json(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min",
            "forecast_days": 3,
            "timezone": "auto",
        },
    )
    current = fc["current"]
    desc = WEATHER_CODES.get(current["weather_code"], "Unknown")
    lines = [
        f"\U0001F324 {name}, {region}",
        f"Now: {current['temperature_2m']}\u00b0C ({desc})",
        f"Feels like: {current['apparent_temperature']}\u00b0C",
        f"Humidity: {current['relative_humidity_2m']}%",
        f"Wind: {current['wind_speed_10m']} km/h",
        "",
        "Next 3 days:",
    ]
    daily = fc["daily"]
    for i in range(len(daily["time"])):
        day = daily["time"][i]
        tmax = daily["temperature_2m_max"][i]
        tmin = daily["temperature_2m_min"][i]
        lines.append(f"{day}: {tmin}\u00b0C / {tmax}\u00b0C")
    return "\n".join(lines)


async def _yahoo_quote(symbol):
    last_error = None
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}?interval=1d&range=1d"
        try:
            data = await _get_json(url, headers=UA)
            meta = data["chart"]["result"][0]["meta"]
            prev = meta.get("previousClose") or meta.get("chartPreviousClose")
            price = meta.get("regularMarketPrice")
            change_pct = meta.get("regularMarketChangePercent")
            if change_pct is None and price and prev:
                change_pct = (price - prev) / prev * 100
            return price, prev, change_pct, meta.get("exchangeName", "")
        except Exception as exc:
            last_error = exc
    raise last_error if last_error else RuntimeError("Yahoo quote failed")


async def get_stocks():
    lines = []
    for symbol, label in (("^BSESN", "Sensex"), ("^NSEI", "Nifty 50")):
        try:
            price, prev, pct, exch = await _yahoo_quote(symbol)
            if price is None:
                lines.append(f"{label}: unavailable")
                continue
            arrow = "\U0001F7E2" if (pct or 0) >= 0 else "\U0001F534"
            lines.append(f"{label}: \u20B9{price:,.2f} {arrow} {pct:+.2f}%")
        except Exception:
            lines.append(f"{label}: unavailable")
    try:
        crypto = await _get_json(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "inr", "include_24hr_change": "true"},
        )
        btc = crypto.get("bitcoin", {})
        eth = crypto.get("ethereum", {})
        btc_pct = btc.get("inr_24h_change", 0)
        eth_pct = eth.get("inr_24h_change", 0)
        b_arrow = "\U0001F7E2" if btc_pct >= 0 else "\U0001F534"
        e_arrow = "\U0001F7E2" if eth_pct >= 0 else "\U0001F534"
        lines.append(f"BTC: \u20B9{btc.get('inr', 0):,.0f} {b_arrow} {btc_pct:+.2f}%")
        lines.append(f"ETH: \u20B9{eth.get('inr', 0):,.0f} {e_arrow} {eth_pct:+.2f}%")
    except Exception:
        lines.append("Crypto: unavailable")
    return "\n".join(lines)


async def get_movies():
    if not TMDB_API_KEY:
        return (
            "Movies need a free TMDB API key (no card).\n"
            "1) Sign up at themoviedb.org -> Settings -> API\n"
            "2) Paste it as TMDB_API_KEY in your .env file"
        )
    data = await _get_json(
        "https://api.themoviedb.org/3/movie/now_playing",
        params={"api_key": TMDB_API_KEY, "region": "IN", "language": "en-IN", "page": 1},
    )
    lines = ["\U0001F3AC Now showing in India:\n"]
    for m in data.get("results", [])[:5]:
        title = m.get("title")
        date = m.get("release_date", "")
        rating = m.get("vote_average", 0)
        bms = f"https://www.google.com/search?q={quote(title + ' bookmyshow')}"
        lines.append(f"* {title} ({date[:4]}) \u2605 {rating:.1f}")
        lines.append(f"  \U0001F3AD {bms}")
    return "\n".join(lines)


async def get_books(query):
    try:
        data = await _get_json(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 5},
        )
        items = data.get("items", [])
        if items:
            lines = [f"\U0001F4DA Books for '{query}':\n"]
            for it in items:
                vi = it.get("volumeInfo", {})
                title = vi.get("title", "?")
                authors = ", ".join(vi.get("authors", []) or ["Unknown"])
                year = vi.get("publishedDate", "?")[:4]
                link = vi.get("infoLink", "")
                lines.append(f"* {title} — {authors} ({year})")
                lines.append(f"  {link}")
            return "\n".join(lines)
    except Exception:
        pass
    try:
        data = await _get_json(
            "https://openlibrary.org/search.json",
            params={"q": query, "limit": 5},
        )
        docs = data.get("docs", [])
        if not docs:
            return f"No books found for '{query}'."
        lines = [f"\U0001F4DA Books for '{query}':\n"]
        for d in docs:
            title = d.get("title", "?")
            authors = ", ".join(d.get("author_name", []) or ["Unknown"])
            year = (d.get("first_publish_year") or "?")
            lines.append(f"* {title} — {authors} ({year})")
        return "\n".join(lines)
    except Exception:
        return f"No books found for '{query}'."


async def get_songs(query):
    data = await _get_json(
        "https://itunes.apple.com/search",
        params={"term": query, "media": "music", "limit": 5},
    )
    results = data.get("results", [])
    if not results:
        return f"No songs found for '{query}'."
    lines = [f"\U0001F3B5 Songs for '{query}':\n"]
    for r in results:
        lines.append(f"* {r.get('trackName')} — {r.get('artistName')}")
        album = r.get("collectionName")
        if album:
            lines.append(f"  Album: {album}")
        preview = r.get("previewUrl")
        if preview:
            lines.append(f"  \U0001F4BF {preview}")
    return "\n".join(lines)


async def get_recipe(ingredients):
    if not ingredients:
        url = "https://www.themealdb.com/api/json/v1/1/random.php"
        params = None
    else:
        url = "https://www.themealdb.com/api/json/v1/1/filter.php"
        params = {"i": ingredients}
    data = await _get_json(url, params=params)
    meals = data.get("meals") or []
    if not meals and ingredients:
        first = ingredients.split(",")[0].strip()
        if first != ingredients:
            url = "https://www.themealdb.com/api/json/v1/1/filter.php"
            params = {"i": first}
            data = await _get_json(url, params=params)
            meals = data.get("meals") or []
    if not meals and ingredients:
        url = "https://www.themealdb.com/api/json/v1/1/search.php"
        params = {"s": ingredients.split(",")[0].strip()}
        data = await _get_json(url, params=params)
        meals = data.get("meals") or []
    if not meals:
        return f"No recipes found with: {ingredients}"
    lines = ["\U0001F35D Recipes:\n"]
    if not ingredients:
        m = meals[0]
        lines.append(f"* {m.get('strMeal')} ({m.get('strArea')})")
        lines.append(f"  {m.get('strYoutube', '')}")
        return "\n".join(lines)
    for m in meals[:6]:
        lines.append(f"* {m.get('strMeal')}")
    return "\n".join(lines)


def translate(text, target):
    from deep_translator import GoogleTranslator

    return GoogleTranslator(source="auto", target=target).translate(text)
