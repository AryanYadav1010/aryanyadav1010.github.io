from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import aiohttp
import asyncio
import ssl
import pycountry

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# NewsAPI configuration
NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY', '')
NEWSAPI_BASE_URL = "https://newsapi.org/v2"

# NewsData.io configuration
NEWSDATA_KEY = os.environ.get('NEWSDATA_KEY', '')
NEWSDATA_BASE_URL = "https://newsdata.io/api/1"

# Create the main app
app = FastAPI(title="Rebalance Global Observatory API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Country code to name mapping (ISO 3166-1 alpha-2)
COUNTRY_DATA = {
    "af": {"name": "Afghanistan", "flag": "🇦🇫"},
    "al": {"name": "Albania", "flag": "🇦🇱"},
    "dz": {"name": "Algeria", "flag": "🇩🇿"},
    "ad": {"name": "Andorra", "flag": "🇦🇩"},
    "ao": {"name": "Angola", "flag": "🇦🇴"},
    "ar": {"name": "Argentina", "flag": "🇦🇷"},
    "am": {"name": "Armenia", "flag": "🇦🇲"},
    "au": {"name": "Australia", "flag": "🇦🇺"},
    "at": {"name": "Austria", "flag": "🇦🇹"},
    "az": {"name": "Azerbaijan", "flag": "🇦🇿"},
    "bs": {"name": "Bahamas", "flag": "🇧🇸"},
    "bh": {"name": "Bahrain", "flag": "🇧🇭"},
    "bd": {"name": "Bangladesh", "flag": "🇧🇩"},
    "by": {"name": "Belarus", "flag": "🇧🇾"},
    "be": {"name": "Belgium", "flag": "🇧🇪"},
    "bz": {"name": "Belize", "flag": "🇧🇿"},
    "bj": {"name": "Benin", "flag": "🇧🇯"},
    "bt": {"name": "Bhutan", "flag": "🇧🇹"},
    "bo": {"name": "Bolivia", "flag": "🇧🇴"},
    "ba": {"name": "Bosnia and Herzegovina", "flag": "🇧🇦"},
    "bw": {"name": "Botswana", "flag": "🇧🇼"},
    "br": {"name": "Brazil", "flag": "🇧🇷"},
    "bn": {"name": "Brunei", "flag": "🇧🇳"},
    "bg": {"name": "Bulgaria", "flag": "🇧🇬"},
    "bf": {"name": "Burkina Faso", "flag": "🇧🇫"},
    "bi": {"name": "Burundi", "flag": "🇧🇮"},
    "kh": {"name": "Cambodia", "flag": "🇰🇭"},
    "cm": {"name": "Cameroon", "flag": "🇨🇲"},
    "ca": {"name": "Canada", "flag": "🇨🇦"},
    "cv": {"name": "Cape Verde", "flag": "🇨🇻"},
    "cf": {"name": "Central African Republic", "flag": "🇨🇫"},
    "td": {"name": "Chad", "flag": "🇹🇩"},
    "cl": {"name": "Chile", "flag": "🇨🇱"},
    "cn": {"name": "China", "flag": "🇨🇳"},
    "co": {"name": "Colombia", "flag": "🇨🇴"},
    "km": {"name": "Comoros", "flag": "🇰🇲"},
    "cg": {"name": "Congo", "flag": "🇨🇬"},
    "cd": {"name": "DR Congo", "flag": "🇨🇩"},
    "cr": {"name": "Costa Rica", "flag": "🇨🇷"},
    "ci": {"name": "Ivory Coast", "flag": "🇨🇮"},
    "hr": {"name": "Croatia", "flag": "🇭🇷"},
    "cu": {"name": "Cuba", "flag": "🇨🇺"},
    "cy": {"name": "Cyprus", "flag": "🇨🇾"},
    "cz": {"name": "Czech Republic", "flag": "🇨🇿"},
    "dk": {"name": "Denmark", "flag": "🇩🇰"},
    "dj": {"name": "Djibouti", "flag": "🇩🇯"},
    "do": {"name": "Dominican Republic", "flag": "🇩🇴"},
    "ec": {"name": "Ecuador", "flag": "🇪🇨"},
    "eg": {"name": "Egypt", "flag": "🇪🇬"},
    "sv": {"name": "El Salvador", "flag": "🇸🇻"},
    "gq": {"name": "Equatorial Guinea", "flag": "🇬🇶"},
    "er": {"name": "Eritrea", "flag": "🇪🇷"},
    "ee": {"name": "Estonia", "flag": "🇪🇪"},
    "sz": {"name": "Eswatini", "flag": "🇸🇿"},
    "et": {"name": "Ethiopia", "flag": "🇪🇹"},
    "fj": {"name": "Fiji", "flag": "🇫🇯"},
    "fi": {"name": "Finland", "flag": "🇫🇮"},
    "fr": {"name": "France", "flag": "🇫🇷"},
    "ga": {"name": "Gabon", "flag": "🇬🇦"},
    "gm": {"name": "Gambia", "flag": "🇬🇲"},
    "ge": {"name": "Georgia", "flag": "🇬🇪"},
    "de": {"name": "Germany", "flag": "🇩🇪"},
    "gh": {"name": "Ghana", "flag": "🇬🇭"},
    "gr": {"name": "Greece", "flag": "🇬🇷"},
    "gd": {"name": "Grenada", "flag": "🇬🇩"},
    "gt": {"name": "Guatemala", "flag": "🇬🇹"},
    "gn": {"name": "Guinea", "flag": "🇬🇳"},
    "gw": {"name": "Guinea-Bissau", "flag": "🇬🇼"},
    "gy": {"name": "Guyana", "flag": "🇬🇾"},
    "ht": {"name": "Haiti", "flag": "🇭🇹"},
    "hn": {"name": "Honduras", "flag": "🇭🇳"},
    "hu": {"name": "Hungary", "flag": "🇭🇺"},
    "is": {"name": "Iceland", "flag": "🇮🇸"},
    "in": {"name": "India", "flag": "🇮🇳"},
    "id": {"name": "Indonesia", "flag": "🇮🇩"},
    "ir": {"name": "Iran", "flag": "🇮🇷"},
    "iq": {"name": "Iraq", "flag": "🇮🇶"},
    "ie": {"name": "Ireland", "flag": "🇮🇪"},
    "il": {"name": "Israel", "flag": "🇮🇱"},
    "it": {"name": "Italy", "flag": "🇮🇹"},
    "jm": {"name": "Jamaica", "flag": "🇯🇲"},
    "jp": {"name": "Japan", "flag": "🇯🇵"},
    "jo": {"name": "Jordan", "flag": "🇯🇴"},
    "kz": {"name": "Kazakhstan", "flag": "🇰🇿"},
    "ke": {"name": "Kenya", "flag": "🇰🇪"},
    "ki": {"name": "Kiribati", "flag": "🇰🇮"},
    "kp": {"name": "North Korea", "flag": "🇰🇵"},
    "kr": {"name": "South Korea", "flag": "🇰🇷"},
    "kw": {"name": "Kuwait", "flag": "🇰🇼"},
    "kg": {"name": "Kyrgyzstan", "flag": "🇰🇬"},
    "la": {"name": "Laos", "flag": "🇱🇦"},
    "lv": {"name": "Latvia", "flag": "🇱🇻"},
    "lb": {"name": "Lebanon", "flag": "🇱🇧"},
    "ls": {"name": "Lesotho", "flag": "🇱🇸"},
    "lr": {"name": "Liberia", "flag": "🇱🇷"},
    "ly": {"name": "Libya", "flag": "🇱🇾"},
    "li": {"name": "Liechtenstein", "flag": "🇱🇮"},
    "lt": {"name": "Lithuania", "flag": "🇱🇹"},
    "lu": {"name": "Luxembourg", "flag": "🇱🇺"},
    "mg": {"name": "Madagascar", "flag": "🇲🇬"},
    "mw": {"name": "Malawi", "flag": "🇲🇼"},
    "my": {"name": "Malaysia", "flag": "🇲🇾"},
    "mv": {"name": "Maldives", "flag": "🇲🇻"},
    "ml": {"name": "Mali", "flag": "🇲🇱"},
    "mt": {"name": "Malta", "flag": "🇲🇹"},
    "mh": {"name": "Marshall Islands", "flag": "🇲🇭"},
    "mr": {"name": "Mauritania", "flag": "🇲🇷"},
    "mu": {"name": "Mauritius", "flag": "🇲🇺"},
    "mx": {"name": "Mexico", "flag": "🇲🇽"},
    "fm": {"name": "Micronesia", "flag": "🇫🇲"},
    "md": {"name": "Moldova", "flag": "🇲🇩"},
    "mc": {"name": "Monaco", "flag": "🇲🇨"},
    "mn": {"name": "Mongolia", "flag": "🇲🇳"},
    "me": {"name": "Montenegro", "flag": "🇲🇪"},
    "ma": {"name": "Morocco", "flag": "🇲🇦"},
    "mz": {"name": "Mozambique", "flag": "🇲🇿"},
    "mm": {"name": "Myanmar", "flag": "🇲🇲"},
    "na": {"name": "Namibia", "flag": "🇳🇦"},
    "nr": {"name": "Nauru", "flag": "🇳🇷"},
    "np": {"name": "Nepal", "flag": "🇳🇵"},
    "nl": {"name": "Netherlands", "flag": "🇳🇱"},
    "nz": {"name": "New Zealand", "flag": "🇳🇿"},
    "ni": {"name": "Nicaragua", "flag": "🇳🇮"},
    "ne": {"name": "Niger", "flag": "🇳🇪"},
    "ng": {"name": "Nigeria", "flag": "🇳🇬"},
    "mk": {"name": "North Macedonia", "flag": "🇲🇰"},
    "no": {"name": "Norway", "flag": "🇳🇴"},
    "om": {"name": "Oman", "flag": "🇴🇲"},
    "pk": {"name": "Pakistan", "flag": "🇵🇰"},
    "pw": {"name": "Palau", "flag": "🇵🇼"},
    "ps": {"name": "Palestine", "flag": "🇵🇸"},
    "pa": {"name": "Panama", "flag": "🇵🇦"},
    "pg": {"name": "Papua New Guinea", "flag": "🇵🇬"},
    "py": {"name": "Paraguay", "flag": "🇵🇾"},
    "pe": {"name": "Peru", "flag": "🇵🇪"},
    "ph": {"name": "Philippines", "flag": "🇵🇭"},
    "pl": {"name": "Poland", "flag": "🇵🇱"},
    "pt": {"name": "Portugal", "flag": "🇵🇹"},
    "qa": {"name": "Qatar", "flag": "🇶🇦"},
    "ro": {"name": "Romania", "flag": "🇷🇴"},
    "ru": {"name": "Russia", "flag": "🇷🇺"},
    "rw": {"name": "Rwanda", "flag": "🇷🇼"},
    "kn": {"name": "Saint Kitts and Nevis", "flag": "🇰🇳"},
    "lc": {"name": "Saint Lucia", "flag": "🇱🇨"},
    "vc": {"name": "Saint Vincent and the Grenadines", "flag": "🇻🇨"},
    "ws": {"name": "Samoa", "flag": "🇼🇸"},
    "sm": {"name": "San Marino", "flag": "🇸🇲"},
    "st": {"name": "Sao Tome and Principe", "flag": "🇸🇹"},
    "sa": {"name": "Saudi Arabia", "flag": "🇸🇦"},
    "sn": {"name": "Senegal", "flag": "🇸🇳"},
    "rs": {"name": "Serbia", "flag": "🇷🇸"},
    "sc": {"name": "Seychelles", "flag": "🇸🇨"},
    "sl": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "sg": {"name": "Singapore", "flag": "🇸🇬"},
    "sk": {"name": "Slovakia", "flag": "🇸🇰"},
    "si": {"name": "Slovenia", "flag": "🇸🇮"},
    "sb": {"name": "Solomon Islands", "flag": "🇸🇧"},
    "so": {"name": "Somalia", "flag": "🇸🇴"},
    "za": {"name": "South Africa", "flag": "🇿🇦"},
    "ss": {"name": "South Sudan", "flag": "🇸🇸"},
    "es": {"name": "Spain", "flag": "🇪🇸"},
    "lk": {"name": "Sri Lanka", "flag": "🇱🇰"},
    "sd": {"name": "Sudan", "flag": "🇸🇩"},
    "sr": {"name": "Suriname", "flag": "🇸🇷"},
    "se": {"name": "Sweden", "flag": "🇸🇪"},
    "ch": {"name": "Switzerland", "flag": "🇨🇭"},
    "sy": {"name": "Syria", "flag": "🇸🇾"},
    "tw": {"name": "Taiwan", "flag": "🇹🇼"},
    "tj": {"name": "Tajikistan", "flag": "🇹🇯"},
    "tz": {"name": "Tanzania", "flag": "🇹🇿"},
    "th": {"name": "Thailand", "flag": "🇹🇭"},
    "tl": {"name": "Timor-Leste", "flag": "🇹🇱"},
    "tg": {"name": "Togo", "flag": "🇹🇬"},
    "to": {"name": "Tonga", "flag": "🇹🇴"},
    "tt": {"name": "Trinidad and Tobago", "flag": "🇹🇹"},
    "tn": {"name": "Tunisia", "flag": "🇹🇳"},
    "tr": {"name": "Turkey", "flag": "🇹🇷"},
    "tm": {"name": "Turkmenistan", "flag": "🇹🇲"},
    "tv": {"name": "Tuvalu", "flag": "🇹🇻"},
    "ug": {"name": "Uganda", "flag": "🇺🇬"},
    "ua": {"name": "Ukraine", "flag": "🇺🇦"},
    "ae": {"name": "United Arab Emirates", "flag": "🇦🇪"},
    "gb": {"name": "United Kingdom", "flag": "🇬🇧"},
    "us": {"name": "United States", "flag": "🇺🇸"},
    "uy": {"name": "Uruguay", "flag": "🇺🇾"},
    "uz": {"name": "Uzbekistan", "flag": "🇺🇿"},
    "vu": {"name": "Vanuatu", "flag": "🇻🇺"},
    "va": {"name": "Vatican City", "flag": "🇻🇦"},
    "ve": {"name": "Venezuela", "flag": "🇻🇪"},
    "vn": {"name": "Vietnam", "flag": "🇻🇳"},
    "ye": {"name": "Yemen", "flag": "🇾🇪"},
    "zm": {"name": "Zambia", "flag": "🇿🇲"},
    "zw": {"name": "Zimbabwe", "flag": "🇿🇼"},
}

# NewsAPI supported countries for top-headlines
NEWSAPI_SUPPORTED_COUNTRIES = [
    'ae', 'ar', 'at', 'au', 'be', 'bg', 'br', 'ca', 'ch', 'cn',
    'co', 'cu', 'cz', 'de', 'eg', 'fr', 'gb', 'gr', 'hk', 'hu',
    'id', 'ie', 'il', 'in', 'it', 'jp', 'kr', 'lt', 'lv', 'ma',
    'mx', 'my', 'ng', 'nl', 'no', 'nz', 'ph', 'pl', 'pt', 'ro',
    'rs', 'ru', 'sa', 'se', 'sg', 'si', 'sk', 'th', 'tr', 'tw',
    'ua', 'us', 've', 'za'
]

# Pydantic Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class ArticleSource(BaseModel):
    id: Optional[str] = None
    name: str

class Article(BaseModel):
    source: ArticleSource
    author: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: str
    urlToImage: Optional[str] = None
    publishedAt: str
    content: Optional[str] = None

class NewsResponse(BaseModel):
    status: str
    total_results: int
    articles: List[Article]
    country_name: str
    country_flag: str

class CountryInfo(BaseModel):
    code: str
    name: str
    flag: str

class CountryListResponse(BaseModel):
    countries: List[CountryInfo]

# Async HTTP session management
_session: Optional[aiohttp.ClientSession] = None

async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=30)
        # Disable SSL verification to work around missing system certs in Python 3.14
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    return _session

async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

# News API Service
async def fetch_news_from_newsapi(
    country_code: str,
    category: Optional[str] = None,
    query: Optional[str] = None,
    indicator: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Helper to fetch from original NewsAPI.org when key is available"""
    if not NEWSAPI_KEY:
        logger.warning("NewsAPI key not configured, returning mock data")
        return generate_mock_news(country_code)

    session = await get_session()

    url = f"{NEWSAPI_BASE_URL}/everything"
    country_name = COUNTRY_DATA.get(country_code.lower(), {}).get("name", country_code)
    search_query = f'"{country_name}"'
    if query:
        search_query = f'{search_query} AND {query}'

    if indicator and indicator in INDICATOR_KEYWORDS:
        indicator_terms = INDICATOR_KEYWORDS[indicator]
        search_query = f'{search_query} AND ({indicator_terms})'
        logger.info(f"Applying indicator keywords for '{indicator}' to news query for {country_name}")

    from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

    params = {
        "apiKey": NEWSAPI_KEY,
        "q": search_query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": min(page_size, 100),
        "page": page,
        "from": from_date
    }

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()

            if data.get("status") != "ok":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"NewsAPI error for {country_name}: {error_msg}")
                return generate_mock_news(country_code)

            if data.get("totalResults", 0) == 0:
                logger.info(f"No news found for {country_name}, returning mock data")
                return generate_mock_news(country_code)

            return data
    except Exception as e:
        logger.error(f"Error fetching news for {country_name}: {str(e)}")
        return generate_mock_news(country_code)


async def fetch_news_from_api(
    country_code: str,
    category: Optional[str] = None,
    query: Optional[str] = None,
    indicator: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Fetch news from NewsData.io (primary) or NewsAPI.org (fallback)"""
    # Simplified indicator keywords for NewsData.io (no exclusions, simpler syntax)
    NEWSDATA_INDICATOR_KEYWORDS = {
        "liberal": "democracy OR \"civil liberties\" OR \"rule of law\" OR \"press freedom\"",
        "gender_inequality": "\"gender equality\" OR \"women's rights\" OR \"equal pay\" OR \"gender gap\"",
        "populism": "populism OR \"far right\" OR nationalism OR \"anti-establishment\"",
        "combined": "governance OR democracy OR \"human rights\" OR \"political stability\"",
    }
    if NEWSDATA_KEY:
        session = await get_session()
        url = f"{NEWSDATA_BASE_URL}/news"
        country_name = COUNTRY_DATA.get(country_code.lower(), {}).get("name", country_code)
        search_query = f'"{country_name}"'
        if query:
            search_query = f'{search_query} AND {query}'

        if indicator and indicator in NEWSDATA_INDICATOR_KEYWORDS:
            indicator_terms = NEWSDATA_INDICATOR_KEYWORDS[indicator]
            search_query = f'{search_query} AND ({indicator_terms})'
            logger.info(f"Applying indicator keywords for '{indicator}' to news query for {country_name} (NewsData.io)")

        params = {
            "apikey": NEWSDATA_KEY,
            "q": search_query,
            "language": "en",
            "country": country_code.lower(),
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"NewsData.io returned status {response.status} for {country_name}")
                    if NEWSAPI_KEY:
                        logger.info("Falling back to NewsAPI.org")
                        return await fetch_news_from_newsapi(country_code, category, query, indicator, page, page_size)
                    return generate_mock_news(country_code)

                data = await response.json()
                if data.get("status") != "success":
                    error_msg = data.get("results", {}).get("message", "Unknown NewsData.io error")
                    logger.error(f"NewsData.io error for {country_name}: {error_msg}")
                    if NEWSAPI_KEY:
                        logger.info("Falling back to NewsAPI.org")
                        return await fetch_news_from_newsapi(country_code, category, query, indicator, page, page_size)
                    return generate_mock_news(country_code)

                results = data.get("results", [])
                if not results:
                    logger.info(f"No news found for {country_name} on NewsData.io")
                    if NEWSAPI_KEY:
                        logger.info("Falling back to NewsAPI.org")
                        return await fetch_news_from_newsapi(country_code, category, query, indicator, page, page_size)
                    return generate_mock_news(country_code)

                mapped_articles = []
                for result in results:
                    mapped_articles.append({
                        "source": {
                            "id": result.get("source_id"),
                            "name": result.get("source_id", "Unknown Source")
                        },
                        "author": result.get("creator", [None])[0] if isinstance(result.get("creator"), list) and result.get("creator") else None,
                        "title": result.get("title", "No Title"),
                        "description": result.get("description"),
                        "url": result.get("link", "#"),
                        "urlToImage": result.get("image_url"),
                        "publishedAt": result.get("pubDate", datetime.now(timezone.utc).isoformat()),
                        "content": result.get("content")
                    })

                total_results = data.get("totalResults", len(mapped_articles))
                return {
                    "status": "ok",
                    "totalResults": total_results,
                    "articles": mapped_articles
                }
        except Exception as e:
            logger.error(f"Error fetching news from NewsData.io for {country_name}: {str(e)}")
            if NEWSAPI_KEY:
                logger.info("Falling back to NewsAPI.org")
                return await fetch_news_from_newsapi(country_code, category, query, indicator, page, page_size)
            return generate_mock_news(country_code)
    else:
        return await fetch_news_from_newsapi(country_code, category, query, indicator, page, page_size)


def generate_mock_news(country_code: str) -> Dict[str, Any]:
    """Generate mock news for demo purposes when API is unavailable"""
    country_info = COUNTRY_DATA.get(country_code.lower(), {"name": country_code.upper(), "flag": ""})
    country_name = country_info["name"]
    
    mock_articles = [
        {
            "source": {"id": "policy-digest", "name": "Policy Digest"},
            "author": "Policy Research Team",
            "title": f"Economic Policy Shifts in {country_name}: A Comprehensive Analysis",
            "description": f"Recent developments in {country_name}'s economic policy landscape indicate significant changes in regulatory frameworks and fiscal strategies.",
            "url": "https://example.com/news/1",
            "urlToImage": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800",
            "publishedAt": datetime.now(timezone.utc).isoformat(),
            "content": f"Policy analysts have noted substantial changes in {country_name}'s approach to economic governance..."
        },
        {
            "source": {"id": "global-affairs", "name": "Global Affairs Weekly"},
            "author": "International Desk",
            "title": f"Diplomatic Relations: {country_name}'s Strategic Partnerships",
            "description": f"An in-depth look at {country_name}'s evolving diplomatic strategies and international alliances.",
            "url": "https://example.com/news/2",
            "urlToImage": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800",
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "content": f"{country_name} has been actively engaging in diplomatic discussions..."
        },
        {
            "source": {"id": "democracy-watch", "name": "Democracy Watch"},
            "author": "Research Division",
            "title": f"Democratic Institutions Under Review in {country_name}",
            "description": f"Examining the state of democratic governance and institutional reforms in {country_name}.",
            "url": "https://example.com/news/3",
            "urlToImage": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800",
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
            "content": f"Recent assessments of {country_name}'s democratic institutions reveal..."
        },
        {
            "source": {"id": "economic-times", "name": "Economic Times Global"},
            "author": "Economics Bureau",
            "title": f"Market Trends: {country_name}'s Financial Sector Outlook",
            "description": f"Analysis of {country_name}'s financial markets and economic indicators for the coming quarter.",
            "url": "https://example.com/news/4",
            "urlToImage": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800",
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
            "content": f"Financial analysts are closely monitoring developments in {country_name}'s markets..."
        },
        {
            "source": {"id": "policy-brief", "name": "Policy Brief International"},
            "author": "Senior Policy Analyst",
            "title": f"Trade Policy Developments in {country_name}",
            "description": f"New trade agreements and policy frameworks shaping {country_name}'s international commerce.",
            "url": "https://example.com/news/5",
            "urlToImage": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800",
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            "content": f"Trade officials have announced new frameworks affecting {country_name}'s export policies..."
        }
    ]
    
    return {
        "status": "ok",
        "totalResults": len(mock_articles),
        "articles": mock_articles
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Rebalance Global Observatory API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

@api_router.get("/countries", response_model=CountryListResponse)
async def get_countries():
    """Get list of all countries with their codes and flags"""
    countries = [
        CountryInfo(code=code, name=data["name"], flag=data["flag"])
        for code, data in sorted(COUNTRY_DATA.items(), key=lambda x: x[1]["name"])
    ]
    return CountryListResponse(countries=countries)

@api_router.get("/country/{country_code}")
async def get_country_info(country_code: str):
    """Get information about a specific country"""
    code = country_code.lower()
    if code not in COUNTRY_DATA:
        raise HTTPException(status_code=404, detail=f"Country code '{country_code}' not found")
    
    data = COUNTRY_DATA[code]
    return {
        "code": code,
        "name": data["name"],
        "flag": data["flag"],
        "newsapi_supported": code in NEWSAPI_SUPPORTED_COUNTRIES
    }

def return_mock_headlines(effective_category: str, page_size: int):
    mock = generate_mock_global_headlines(effective_category)
    return {
        "status": "ok",
        "total_results": mock["totalResults"],
        "articles": mock["articles"][:page_size],
        "category": effective_category,
        "is_mock": True
    }


async def get_newsapi_top_headlines(country: str, category: Optional[str], page_size: int, effective_category: str):
    if not NEWSAPI_KEY:
        logger.info("NewsAPI key not configured, returning mock headlines")
        return return_mock_headlines(effective_category, page_size)

    session = await get_session()
    url = f"{NEWSAPI_BASE_URL}/top-headlines"

    params = {
        "apiKey": NEWSAPI_KEY,
        "country": country.lower(),
        "pageSize": min(page_size, 100),
    }
    if category:
        params["category"] = category

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()

            if data.get("status") != "ok":
                logger.error(f"NewsAPI headlines error: {data.get('message')}")
                return return_mock_headlines(effective_category, page_size)

            return {
                "status": "ok",
                "total_results": data.get("totalResults", 0),
                "articles": data.get("articles", []),
                "category": effective_category,
                "is_mock": False
            }
    except Exception as e:
        logger.error(f"Error fetching top headlines: {str(e)}")
        return return_mock_headlines(effective_category, page_size)


@api_router.get("/news/top-headlines")
async def get_top_headlines(
    country: str = Query("us", description="Country code for headlines"),
    category: Optional[str] = Query(None, description="Category: general, business, technology, science, health"),
    page_size: int = Query(12, ge=1, le=50)
):
    """Get top headlines — global latest news"""
    effective_category = category or "general"

    if NEWSDATA_KEY:
        session = await get_session()
        url = f"{NEWSDATA_BASE_URL}/latest"

        params = {
            "apikey": NEWSDATA_KEY,
            "country": country.lower(),
            "language": "en",
        }
        if category:
            params["category"] = category

        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"NewsData.io headlines returned status {response.status}")
                    if NEWSAPI_KEY:
                        logger.info("Falling back to NewsAPI.org for top headlines")
                        return await get_newsapi_top_headlines(country, category, page_size, effective_category)
                    return return_mock_headlines(effective_category, page_size)

                data = await response.json()
                if data.get("status") != "success":
                    error_msg = data.get("results", {}).get("message", "Unknown error")
                    logger.error(f"NewsData.io headlines error: {error_msg}")
                    if NEWSAPI_KEY:
                        logger.info("Falling back to NewsAPI.org for top headlines")
                        return await get_newsapi_top_headlines(country, category, page_size, effective_category)
                    return return_mock_headlines(effective_category, page_size)

                results = data.get("results", [])
                mapped_articles = []
                for result in results:
                    mapped_articles.append({
                        "source": {
                            "id": result.get("source_id"),
                            "name": result.get("source_id", "Unknown Source")
                        },
                        "author": result.get("creator", [None])[0] if isinstance(result.get("creator"), list) and result.get("creator") else None,
                        "title": result.get("title", "No Title"),
                        "description": result.get("description"),
                        "url": result.get("link", "#"),
                        "urlToImage": result.get("image_url"),
                        "publishedAt": result.get("pubDate", datetime.now(timezone.utc).isoformat()),
                        "content": result.get("content")
                    })

                return {
                    "status": "ok",
                    "total_results": data.get("totalResults", len(mapped_articles)),
                    "articles": mapped_articles[:page_size],
                    "category": effective_category,
                    "is_mock": False
                }
        except Exception as e:
            logger.error(f"Error fetching top headlines from NewsData.io: {str(e)}")
            if NEWSAPI_KEY:
                logger.info("Falling back to NewsAPI.org for top headlines")
                return await get_newsapi_top_headlines(country, category, page_size, effective_category)
            return return_mock_headlines(effective_category, page_size)
    else:
        return await get_newsapi_top_headlines(country, category, page_size, effective_category)

@api_router.get("/news/{country_code}", response_model=NewsResponse)
async def get_country_news(
    country_code: str,
    category: Optional[str] = Query(None, description="News category: business, technology, politics, etc."),
    query: Optional[str] = Query(None, description="Search query within news"),
    indicator: Optional[str] = Query(None, description="Indicator id (liberal, gender_inequality, populism, combined) to filter news by topic"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Number of articles per page")
):
    """Get news for a specific country"""
    code = country_code.lower()
    
    # Get country info
    country_info = COUNTRY_DATA.get(code, {"name": country_code.upper(), "flag": ""})
    
    # Fetch news
    news_data = await fetch_news_from_api(
        country_code=code,
        category=category,
        query=query,
        indicator=indicator,
        page=page,
        page_size=page_size
    )
    
    # Parse articles
    articles = []
    for article_data in news_data.get("articles", []):
        try:
            # Handle None values gracefully
            source_data = article_data.get("source", {})
            if source_data is None:
                source_data = {}
            
            article = Article(
                source=ArticleSource(
                    id=source_data.get("id"),
                    name=source_data.get("name", "Unknown Source")
                ),
                author=article_data.get("author"),
                title=article_data.get("title", "No Title"),
                description=article_data.get("description"),
                url=article_data.get("url", "#"),
                urlToImage=article_data.get("urlToImage"),
                publishedAt=article_data.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                content=article_data.get("content")
            )
            articles.append(article)
        except Exception as e:
            logger.warning(f"Error parsing article: {e}")
            continue
    
    return NewsResponse(
        status="ok",
        total_results=news_data.get("totalResults", len(articles)),
        articles=articles,
        country_name=country_info["name"],
        country_flag=country_info["flag"]
    )

# Global top headlines
def generate_mock_global_headlines(category: str = "general") -> Dict[str, Any]:
    """Generate mock global headlines for demo purposes"""
    categories_data = {
        "general": [
            {"title": "Global Summit Addresses Climate Change and Economic Recovery", "source": "World Policy Review", "desc": "World leaders convene to discuss coordinated responses to climate change while balancing economic growth objectives."},
            {"title": "UN Report Highlights Progress in Sustainable Development Goals", "source": "Global Affairs Daily", "desc": "New data shows mixed progress across the 17 SDGs, with significant gains in some regions and setbacks in others."},
            {"title": "International Trade Agreements Reshape Global Supply Chains", "source": "Economic Times Global", "desc": "Recent bilateral and multilateral trade deals are fundamentally altering how goods move across borders."},
            {"title": "Digital Governance Frameworks Gain Momentum Worldwide", "source": "Tech Policy Forum", "desc": "Countries are increasingly adopting digital governance frameworks to modernize public services."},
            {"title": "Global Health Initiative Launches New Pandemic Preparedness Fund", "source": "Health Policy Watch", "desc": "A coalition of nations establishes a $10 billion fund to strengthen global health infrastructure."},
            {"title": "Democracy Index Shows Shifts Across Multiple Regions", "source": "Democracy Watch", "desc": "Annual assessment reveals changing patterns in democratic governance across Europe, Asia, and Africa."},
        ],
        "business": [
            {"title": "Global Markets Rally on Positive Economic Data", "source": "Financial Times", "desc": "Stock markets worldwide surge as employment and manufacturing data exceed expectations."},
            {"title": "Central Banks Signal New Monetary Policy Direction", "source": "Bloomberg", "desc": "Major central banks hint at coordinated shifts in interest rate policies."},
            {"title": "Emerging Markets Attract Record Foreign Investment", "source": "Reuters", "desc": "Developing economies see unprecedented capital inflows as investors seek growth opportunities."},
            {"title": "Tech Giants Report Strong Quarterly Earnings", "source": "CNBC", "desc": "Major technology companies exceed analyst expectations in latest earnings reports."},
            {"title": "Green Bonds Market Reaches New Milestone", "source": "ESG Investor", "desc": "Sustainable finance instruments hit record issuance levels as ESG investing gains traction."},
            {"title": "Supply Chain Innovation Drives Manufacturing Renaissance", "source": "Industry Week", "desc": "New technologies and nearshoring trends are reshaping global manufacturing landscapes."},
        ],
        "technology": [
            {"title": "AI Regulation Frameworks Emerge Across Major Economies", "source": "TechCrunch", "desc": "Governments worldwide are crafting new rules to govern artificial intelligence deployment."},
            {"title": "Quantum Computing Breakthrough Promises Real-World Applications", "source": "Wired", "desc": "Researchers achieve new milestones in quantum error correction, bringing practical quantum computing closer."},
            {"title": "Cybersecurity Spending Surges Amid Rising Threat Landscape", "source": "CyberScoop", "desc": "Organizations worldwide are dramatically increasing cybersecurity budgets."},
            {"title": "5G Expansion Accelerates in Developing Nations", "source": "Telecom Review", "desc": "Next-generation cellular networks reach new markets, enabling digital transformation."},
            {"title": "Open Source AI Models Challenge Big Tech Dominance", "source": "The Verge", "desc": "Community-developed AI models are narrowing the gap with proprietary systems."},
            {"title": "Digital Identity Systems Transform Government Services", "source": "GovTech", "desc": "National digital ID programs streamline citizen access to public services."},
        ],
        "science": [
            {"title": "Climate Scientists Report Critical Ocean Temperature Data", "source": "Nature", "desc": "New measurements reveal accelerating changes in ocean heat content."},
            {"title": "Space Agencies Collaborate on Lunar Exploration Mission", "source": "Space News", "desc": "International partnership announced for ambitious Moon research program."},
            {"title": "Breakthrough in Renewable Energy Storage Technology", "source": "Science Daily", "desc": "Novel battery chemistry promises to solve intermittency challenges for solar and wind power."},
            {"title": "Biodiversity Study Reveals New Species in Deep Ocean", "source": "National Geographic", "desc": "Marine expedition discovers dozens of previously unknown species."},
            {"title": "Gene Therapy Advances Offer Hope for Rare Diseases", "source": "The Lancet", "desc": "Clinical trials show promising results for genetic treatments targeting inherited conditions."},
            {"title": "Arctic Research Station Reports Record Environmental Changes", "source": "Climate Central", "desc": "Long-term monitoring data reveals unprecedented shifts in Arctic ecosystem."},
        ],
        "health": [
            {"title": "WHO Launches Global Health Equity Initiative", "source": "WHO News", "desc": "New program aims to reduce healthcare disparities between nations."},
            {"title": "Mental Health Support Programs Expand Worldwide", "source": "Health Affairs", "desc": "Countries invest in mental health infrastructure following increased awareness."},
            {"title": "Vaccine Development Platform Shows Promise for Multiple Diseases", "source": "STAT News", "desc": "Flexible vaccine technology could accelerate response to future health threats."},
            {"title": "Telemedicine Adoption Transforms Rural Healthcare Access", "source": "mHealth News", "desc": "Remote medical consultations bridge gaps in underserved communities."},
            {"title": "Global Nutrition Study Links Diet to Long-Term Health Outcomes", "source": "BMJ", "desc": "Large-scale research reveals connections between dietary patterns and disease prevention."},
            {"title": "Air Quality Improvements Show Measurable Health Benefits", "source": "Env Health Perspectives", "desc": "Cities with cleaner air report significant reductions in respiratory conditions."},
        ],
    }

    articles_data = categories_data.get(category, categories_data["general"])
    
    mock_articles = []
    images = [
        "https://images.unsplash.com/photo-1504711434969-e33886168d6c?w=800",
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=800",
        "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800",
        "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800",
    ]
    
    for i, article in enumerate(articles_data):
        mock_articles.append({
            "source": {"id": None, "name": article["source"]},
            "author": "Staff Reporter",
            "title": article["title"],
            "description": article["desc"],
            "url": f"https://example.com/news/{category}/{i+1}",
            "urlToImage": images[i % len(images)],
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=i * 2)).isoformat(),
            "content": article["desc"]
        })
    
    return {
        "status": "ok",
        "totalResults": len(mock_articles),
        "articles": mock_articles
    }


@api_router.get("/search/news")
async def search_news(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """Search news globally"""
    if not NEWSAPI_KEY:
        return {
            "status": "ok",
            "total_results": 0,
            "articles": [],
            "message": "NewsAPI key not configured"
        }
    
    session = await get_session()
    url = f"{NEWSAPI_BASE_URL}/everything"
    
    from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    
    params = {
        "apiKey": NEWSAPI_KEY,
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": min(page_size, 100),
        "page": page,
        "from": from_date
    }
    
    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            
            if data.get("status") != "ok":
                return {
                    "status": "error",
                    "total_results": 0,
                    "articles": [],
                    "message": data.get("message", "Search failed")
                }
            
            return {
                "status": "ok",
                "total_results": data.get("totalResults", 0),
                "articles": data.get("articles", [])
            }
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {
            "status": "error",
            "total_results": 0,
            "articles": [],
            "message": str(e)
        }

# Load all indicator data
import json

INDICATORS_DATA = {}
INDICATOR_METADATA = {
    "liberal": {
        "name": "Liberal Democracy",
        "description": "Measures liberal democracy based on civil liberties and rule of law",
        "source": "V-Dem v2x_liberal",
        "lower_is_better": False
    },
    "gender_inequality": {
        "name": "Gender Inequality",
        "description": "Gender Inequality Index (GII) - lower values mean less inequality",
        "source": "UNDP HDR 2023",
        "lower_is_better": True
    },
    "populism": {
        "name": "Populism",
        "description": "Weighted populism score based on party populism and vote share",
        "source": "Global Party Survey 2020",
        "lower_is_better": True,
    },
    "combined": {
        "name": "Combined Index",
        "description": "Combined score from Liberal Democracy, Gender Equality, and Low Populism",
        "source": "Composite Index",
        "lower_is_better": False
    }
}

# Indicator-specific search keywords for news filtering
INDICATOR_KEYWORDS = {
    # Liberal Democracy — shortened to fit 500 char limit
    "liberal": (
        '((democracy OR "civil liberties" OR "rule of law" OR "human rights" OR elections '
        'OR "press freedom" OR "political rights" OR "free speech" OR "judicial independence" '
        'OR "democratic backsliding" OR "civil society" OR "freedom of expression") '
        'AND (politics OR government OR governance)) '
        '-sports -football -soccer -basketball -tennis -cricket '
        '-entertainment -celebrity -music -movie -recipe -fashion -gaming -weather'
    ),
    # Gender Inequality — shortened to fit 500 char limit
    "gender_inequality": (
        '(( "gender equality" OR "women\'s rights" OR feminism OR discrimination '
        'OR "gender gap" OR "reproductive rights" OR "gender-based violence" '
        'OR "equal pay" OR "women in politics" OR "maternal health" OR "gender parity") '
        'AND (policy OR rights OR society)) '
        '-sports -entertainment -celebrity -music -movie -recipe -fashion -gaming -weather'
    ),
    # Populism — shortened to fit 500 char limit
    "populism": (
        '((populism OR "far right" OR "far left" OR "political polarization" '
        'OR nationalism OR authoritarian OR "anti-establishment" OR "democratic erosion" '
        'OR "illiberal democracy" OR "political extremism") '
        'AND (politics OR movement OR party)) '
        '-sports -entertainment -celebrity -music -movie -recipe -fashion -gaming -weather'
    ),
    # Combined — shortened to fit 500 char limit
    "combined": (
        '((governance OR democracy OR "human rights" OR policy OR "civil society" '
        'OR "rule of law" OR "political stability" OR "institutional reform") '
        'AND (government OR politics OR international)) '
        '-sports -entertainment -celebrity -music -movie -recipe -fashion -gaming -weather'
    ),
}

try:
    indicators_path = ROOT_DIR / 'indicators_data.json'
    if indicators_path.exists():
        with open(indicators_path, 'r') as f:
            INDICATORS_DATA = json.load(f)
        # Remove old keys we no longer use
        for old_key in ['gender', 'egalitarian']:
            if old_key in INDICATORS_DATA:
                del INDICATORS_DATA[old_key]
        for key, data in INDICATORS_DATA.items():
            logger.info(f"Loaded {key} data for {len(data)} countries")
except Exception as e:
    logger.error(f"Failed to load indicators data: {e}")

# Load Gender Inequality Index from separate file
try:
    gii_path = ROOT_DIR / 'gender_inequality_index.json'
    if gii_path.exists():
        with open(gii_path, 'r') as f:
            INDICATORS_DATA['gender_inequality'] = json.load(f)
        logger.info(f"Loaded gender inequality data for {len(INDICATORS_DATA['gender_inequality'])} countries")
except Exception as e:
    logger.error(f"Failed to load gender inequality data: {e}")

# Load Populism Index from pre-built file (ISO-3 keyed, same format as liberal/gender)
try:
    pop_path = ROOT_DIR / 'populism_index.json'
    if pop_path.exists():
        with open(pop_path, 'r') as f:
            INDICATORS_DATA['populism'] = json.load(f)
        logger.info(f"Loaded populism data for {len(INDICATORS_DATA['populism'])} countries")
    else:
        logger.warning("populism_index.json not found, skipping populism indicator")
except Exception as e:
    logger.error(f"Failed to load populism data: {e}")

# Build Combined Index from available indicators
# Combined = average of (liberal_dem, 1 - gender_inequality, 1 - populism)
# Higher combined = better overall governance
try:
    combined_data = {}
    liberal_data = INDICATORS_DATA.get('liberal', {})
    gender_data = INDICATORS_DATA.get('gender_inequality', {})
    populism_data = INDICATORS_DATA.get('populism', {})

    logger.info(f"Building combined index from {len(liberal_data)} liberal, {len(gender_data)} gender, {len(populism_data)} populism entries")

    # Get all country codes across all indicators
    all_codes = set()
    for dataset in [liberal_data, gender_data, populism_data]:
        all_codes.update(dataset.keys())

    for code in all_codes:
        scores = []
        # Liberal Democracy: higher = better (use as-is)
        if code in liberal_data:
            scores.append(liberal_data[code]['value'])
        # Gender Inequality: lower = better (invert)
        if code in gender_data:
            scores.append(1.0 - gender_data[code]['value'])
        # Populism: higher = more populist (invert so lower populism = better)
        if code in populism_data:
            scores.append(1.0 - populism_data[code]['value'])

        if len(scores) == 3:  # Strictly require all 3 indicators
            avg = sum(scores) / len(scores)
            # Get name from any available source
            name = (liberal_data.get(code, {}).get('name') or
                    gender_data.get(code, {}).get('name') or
                    populism_data.get(code, {}).get('name', code))
            combined_data[code] = {
                "name": name,
                "value": round(avg, 3),
                "year": 2024
            }

    if combined_data:
        INDICATORS_DATA['combined'] = combined_data
        logger.info(f"Built combined index for {len(combined_data)} countries")
    else:
        logger.warning("Combined index is empty — check that liberal, gender_inequality, and populism data are all loaded with matching country codes")
except Exception as e:
    logger.error(f"Failed to build combined index: {e}")

# Fallback to old liberal index if new file doesn't exist
if not INDICATORS_DATA:
    try:
        liberal_index_path = ROOT_DIR / 'liberal_index.json'
        if liberal_index_path.exists():
            with open(liberal_index_path, 'r') as f:
                INDICATORS_DATA['liberal'] = json.load(f)
            logger.info(f"Loaded liberal index data for {len(INDICATORS_DATA['liberal'])} countries")
    except Exception as e:
        logger.error(f"Failed to load liberal index data: {e}")

# V-Dem country code (ISO 3166-1 alpha-3) to alpha-2 mapping
VDEM_TO_ALPHA2 = {
    "AFG": "af", "ALB": "al", "DZA": "dz", "AND": "ad", "AGO": "ao",
    "ARG": "ar", "ARM": "am", "AUS": "au", "AUT": "at", "AZE": "az",
    "BHS": "bs", "BHR": "bh", "BGD": "bd", "BRB": "bb", "BLR": "by",
    "BEL": "be", "BLZ": "bz", "BEN": "bj", "BTN": "bt", "BOL": "bo",
    "BIH": "ba", "BWA": "bw", "BRA": "br", "BRN": "bn", "BGR": "bg",
    "BFA": "bf", "BDI": "bi", "CPV": "cv", "KHM": "kh", "CMR": "cm",
    "CAN": "ca", "CAF": "cf", "TCD": "td", "CHL": "cl", "CHN": "cn",
    "COL": "co", "COM": "km", "COG": "cg", "COD": "cd", "CRI": "cr",
    "CIV": "ci", "HRV": "hr", "CUB": "cu", "CYP": "cy", "CZE": "cz",
    "DNK": "dk", "DJI": "dj", "DMA": "dm", "DOM": "do", "ECU": "ec",
    "EGY": "eg", "SLV": "sv", "GNQ": "gq", "ERI": "er", "EST": "ee",
    "SWZ": "sz", "ETH": "et", "FJI": "fj", "FIN": "fi", "FRA": "fr",
    "GAB": "ga", "GMB": "gm", "GEO": "ge", "DEU": "de", "GHA": "gh",
    "GRC": "gr", "GRD": "gd", "GTM": "gt", "GIN": "gn", "GNB": "gw",
    "GUY": "gy", "HTI": "ht", "HND": "hn", "HUN": "hu", "ISL": "is",
    "IND": "in", "IDN": "id", "IRN": "ir", "IRQ": "iq", "IRL": "ie",
    "ISR": "il", "ITA": "it", "JAM": "jm", "JPN": "jp", "JOR": "jo",
    "KAZ": "kz", "KEN": "ke", "KIR": "ki", "PRK": "kp", "KOR": "kr",
    "KWT": "kw", "KGZ": "kg", "LAO": "la", "LVA": "lv", "LBN": "lb",
    "LSO": "ls", "LBR": "lr", "LBY": "ly", "LIE": "li", "LTU": "lt",
    "LUX": "lu", "MDG": "mg", "MWI": "mw", "MYS": "my", "MDV": "mv",
    "MLI": "ml", "MLT": "mt", "MHL": "mh", "MRT": "mr", "MUS": "mu",
    "MEX": "mx", "FSM": "fm", "MDA": "md", "MCO": "mc", "MNG": "mn",
    "MNE": "me", "MAR": "ma", "MOZ": "mz", "MMR": "mm", "NAM": "na",
    "NRU": "nr", "NPL": "np", "NLD": "nl", "NZL": "nz", "NIC": "ni",
    "NER": "ne", "NGA": "ng", "MKD": "mk", "NOR": "no", "OMN": "om",
    "PAK": "pk", "PLW": "pw", "PSE": "ps", "PAN": "pa", "PNG": "pg",
    "PRY": "py", "PER": "pe", "PHL": "ph", "POL": "pl", "PRT": "pt",
    "QAT": "qa", "ROU": "ro", "RUS": "ru", "RWA": "rw", "KNA": "kn",
    "LCA": "lc", "VCT": "vc", "WSM": "ws", "SMR": "sm", "STP": "st",
    "SAU": "sa", "SEN": "sn", "SRB": "rs", "SYC": "sc", "SLE": "sl",
    "SGP": "sg", "SVK": "sk", "SVN": "si", "SLB": "sb", "SOM": "so",
    "ZAF": "za", "SSD": "ss", "ESP": "es", "LKA": "lk", "SDN": "sd",
    "SUR": "sr", "SWE": "se", "CHE": "ch", "SYR": "sy", "TWN": "tw",
    "TJK": "tj", "TZA": "tz", "THA": "th", "TLS": "tl", "TGO": "tg",
    "TON": "to", "TTO": "tt", "TUN": "tn", "TUR": "tr", "TKM": "tm",
    "TUV": "tv", "UGA": "ug", "UKR": "ua", "ARE": "ae", "GBR": "gb",
    "USA": "us", "URY": "uy", "UZB": "uz", "VUT": "vu", "VAT": "va",
    "VEN": "ve", "VNM": "vn", "YEM": "ye", "ZMB": "zm", "ZWE": "zw",
}

def get_bucket(value: float) -> int:
    """Get bucket index (0-3) for a value between 0-1"""
    if value < 0.25:
        return 0
    elif value < 0.5:
        return 1
    elif value < 0.75:
        return 2
    else:
        return 3

@api_router.get("/indicators")
async def get_available_indicators():
    """Get list of available indicators"""
    return {
        "indicators": [
            {"id": key, **meta} 
            for key, meta in INDICATOR_METADATA.items()
            if key in INDICATORS_DATA
        ]
    }

@api_router.get("/indicators/{indicator_id}")
async def get_indicator_data(indicator_id: str):
    """Get data for a specific indicator"""
    if indicator_id not in INDICATORS_DATA:
        raise HTTPException(status_code=404, detail=f"Indicator '{indicator_id}' not found")
    
    indicator_data = INDICATORS_DATA[indicator_id]
    result = {}
    
    for vdem_code, data in indicator_data.items():
        alpha2 = VDEM_TO_ALPHA2.get(vdem_code, vdem_code.lower())
        result[alpha2] = {
            "name": data["name"],
            "value": data["value"],
            "year": data["year"],
            "bucket": get_bucket(data["value"])
        }
    
    metadata = INDICATOR_METADATA.get(indicator_id, {})
    
    return {
        "data": result,
        "metadata": {
            "id": indicator_id,
            "name": metadata.get("name", indicator_id),
            "description": metadata.get("description", ""),
            "source": metadata.get("source", "V-Dem Dataset v15"),
            "scale": {"min": 0, "max": 1}
        }
    }

@api_router.get("/liberal-index")
async def get_liberal_index():
    """Get Liberal Democracy Index data (backward compatible)"""
    return await get_indicator_data("liberal")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_session()
    client.close()
    logger.info("Application shutdown complete")
