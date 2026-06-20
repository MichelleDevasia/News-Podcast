import streamlit as st
import requests
from deep_translator import GoogleTranslator
from datetime import datetime
import io
import re
import xml.etree.ElementTree as ET
import urllib.parse
from gtts import gTTS

# --- CONFIGURATION & HARDCODED API KEY ---
NEWSDATA_API_KEY = "pub_36a7f0de480e4be6b9861d814c0b5f02"

# Set page config for a premium look
st.set_page_config(
    page_title="News Podcast & API Tester",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium custom CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8F8F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #7f8c8d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Premium Article Card styling */
    .article-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stApp {
        background-attachment: fixed;
    }
    
    /* Support light mode with readable colors */
    @media (prefers-color-scheme: light) {
        .article-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
    }
    
    .article-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
        border-color: #FF4B4B;
    }
    
    .article-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    
    .article-title a {
        text-decoration: none;
        color: inherit;
        transition: color 0.2s ease;
    }
    
    .article-title a:hover {
        color: #FF4B4B;
    }
    
    .meta-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.8rem;
    }
    
    .badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.6rem;
        border-radius: 50px;
        font-weight: 600;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .badge-category {
        background-color: rgba(255, 75, 75, 0.15);
        color: #FF4B4B;
    }
    
    .badge-country {
        background-color: rgba(9, 132, 227, 0.15);
        color: #0984e3;
    }
    
    .badge-source {
        background-color: rgba(108, 92, 231, 0.15);
        color: #6c5ce7;
    }
    
    .badge-score {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
    }
    
    .article-date {
        font-size: 0.85rem;
        color: #95a5a6;
        margin-top: 0.5rem;
    }
    
    .description-text {
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.5em;
        height: 4.5em;
    }
</style>
""", unsafe_allow_html=True)

# List of trusted source patterns to boost
TRUSTED_SOURCE_SUBSTRINGS = [
    "bbc", "dw", "deutsche welle", "financial times", "nytimes", "new york times", 
    "guardian", "al jazeera", "aljazeera", "economist", "mit technology review", 
    "nature", "the hindu", "thehindu", "indian express", "indianexpress", 
    "ndtv", "hindustan times", "hindustantimes", "times of india", "timesofindia", 
    "economic times", "economictimes", "livemint", "mint", "business standard", 
    "businessstandard", "the print", "theprint", "newslaundry", "the wire", "thewire", 
    "scroll.in", "scroll", "factchecker", "alt news", "altnews", "manorama", 
    "mathrubhumi", "prajavani", "vijayavani", "dailythanthi", "dina thanthi", "dinamalar"
]

# Helper function to translate text to a target language
def translate_to_target_lang(text, target_lang):
    if not text or not text.strip():
        return text
    try:
        if target_lang == 'en':
            if any(ord(char) > 127 for char in text):
                return GoogleTranslator(source='auto', target='en').translate(text)
            return text
        else:
            return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception:
        pass
    return text

# Jaccard similarity de-duplicator helper
def is_similar_to_existing(title, existing_titles, threshold=0.45):
    if not title or not title.strip():
        return False
        
    def clean_and_tokenize(text):
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are", "was", "were", "of", "by", "that", "this", "these", "those", "it", "its", "from", "on", "about", "against"}
        words = re.findall(r'\b\w+\b', text.lower())
        return set(w for w in words if w not in stopwords and len(w) > 2)

    title_words = clean_and_tokenize(title)
    if not title_words:
        return False
        
    for exist in existing_titles:
        exist_words = clean_and_tokenize(exist)
        if not exist_words:
            continue
            
        intersection = len(title_words.intersection(exist_words))
        union = len(title_words.union(exist_words))
        if union > 0:
            jaccard = intersection / union
            if jaccard >= threshold:
                return True
    return False

# Local extractive summarizer parsing text using local rules (2-3 sentences)
def summarize_text_concise(title, description, content):
    text_source = description if description and len(description.strip()) > 30 else content
    if not text_source or not text_source.strip():
        text_source = title
        
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text_source.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 8]
    
    if not sentences:
        return title or "No summary available."
        
    # Return first 3 sentences
    return " ".join(sentences[:3])

# Google News RSS Fetcher (Outside Source Fallback)
def fetch_google_news(query_text, country_code, lang_code="en"):
    hl = "en"
    gl = "US"
    ceid = "US:en"
    
    if country_code == "in":
        hl = "en-IN" if lang_code == "en" else lang_code
        gl = "IN"
        ceid = f"IN:{hl}"
    elif country_code == "us":
        gl = "US"
        hl = "en"
        ceid = "US:en"
    elif country_code == "gb":
        gl = "GB"
        hl = "en-GB"
        ceid = "GB:en"
        
    encoded_q = urllib.parse.quote(query_text)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={gl}&ceid={ceid}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            articles = []
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
                description = item.find("description").text if item.find("description") is not None else ""
                
                source_id = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source_id = parts[1]
                    
                description_clean = re.sub(r'<[^>]*>', '', description)
                
                try:
                    dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                    formatted_pub_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    formatted_pub_date = pub_date_str
                
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description_clean,
                    "pubDate": formatted_pub_date,
                    "source_id": source_id,
                    "category": ["general"],
                    "country": [country_code]
                })
            return articles
    except Exception:
        pass
    return []

# Helper to calculate news sentiment scoring
def get_news_sentiment(title, description):
    text = (title + " " + description).lower()
    
    negative_words = {"kill", "die", "crash", "dead", "arrest", "scam", "crisis", "fire", "threat", 
                      "clash", "loss", "inflation", "protest", "strike", "court", "accuse", "warn", "suspect"}
                      
    positive_words = {"win", "gain", "grow", "success", "launch", "develop", "benefit", "celebrate", 
                      "support", "peace", "summit", "achieve", "rescue", "save", "profit", "boost"}
                      
    words = set(re.findall(r'\b\w+\b', text))
    neg_hits = len(words.intersection(negative_words))
    pos_hits = len(words.intersection(positive_words))
    
    if neg_hits > pos_hits:
        return "Negative"
    elif pos_hits > neg_hits:
        return "Positive"
    else:
        return "Neutral"

# Dual-Host Audio Generation Helper (voice modulation by alternating accents/speeds)
def generate_dual_host_audio(segments, lang_code, accent_tld):
    combined_bytes = b""
    for text, host_num in segments:
        try:
            if lang_code == "en":
                # Alternate TLDs for English (US vs UK accent)
                current_tld = accent_tld if host_num == 0 else "co.uk"
                tts = gTTS(text=text, lang=lang_code, tld=current_tld, slow=False)
            else:
                # Alternate speeds for non-English languages
                current_slow = False if host_num == 0 else True
                tts = gTTS(text=text, lang=lang_code, slow=current_slow)
            
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            combined_bytes += fp.getvalue()
        except Exception:
            pass
            
    if combined_bytes:
        return io.BytesIO(combined_bytes)
    return None

# gTTS single-speaker audio generator
def generate_audio(text, lang='en', tld='com'):
    try:
        if lang == 'en':
            tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        else:
            tts = gTTS(text=text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"TTS Error: {e}")
        return None

# Date parsing helper
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

# Composite scoring function to rank article by Importance + Recency + Trusted Source Boost
def calculate_article_score(article, user_query, cat_keywords):
    score = 0.0
    title = (article.get("title") or "").lower()
    description = (article.get("description") or "").lower()
    content = (article.get("content") or "").lower()
    source_id = str(article.get("source_id") or "").lower()
    
    # 1. Trusted Source Boost (Float priority sources to top)
    is_trusted = False
    for ts in TRUSTED_SOURCE_SUBSTRINGS:
        if ts in source_id:
            is_trusted = True
            break
    if is_trusted:
        score += 45.0
        
    # 2. Importance matching (User Query)
    if user_query:
        uq = user_query.lower()
        if uq in title:
            score += 20.0
        elif uq in description:
            score += 7.0
        elif uq in content:
            score += 3.0
            
    # 3. Importance matching (Category Keywords)
    for kw in cat_keywords:
        kw_l = kw.lower()
        if kw_l in title:
            score += 10.0
        elif kw_l in description:
            score += 4.0
            
    # 4. Recency Boost (Freshness)
    pub_date_str = article.get("pubDate")
    if pub_date_str:
        pub_dt = parse_date(pub_date_str)
        now = datetime.now()
        elapsed_hours = (now - pub_dt).total_seconds() / 3600.0
        if elapsed_hours < 0:
            elapsed_hours = 0
            
        recency_score = 30.0 / (1.0 + (elapsed_hours / 12.0))
        score += recency_score
        
    return round(score, 1)

# Main Title Header
st.markdown("<h1 class='main-title'>🎙️ News Podcast & API Tester</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Convert matching news articles from NewsData.io into customizable podcast briefs.</p>", unsafe_allow_html=True)

# Mapping of custom user-friendly categories to NewsData.io API categories and keywords
CUSTOM_CATEGORIES = {
    "General": {
        "api_category": None,
        "keywords": ["news", "update", "latest", "today", "report"]
    },
    "Politics & Governance": {
        "api_category": "politics",
        "keywords": ["politics", "election", "political party", "assembly", "policy", "government scheme", "minister", "parliament", "governance"]
    },
    "Crime & Public Safety": {
        "api_category": None,
        "keywords": ["crime", "police", "investigation", "scam", "arrest", "law enforcement", "safety", "threat", "robbery", "theft", "murder"]
    },
    "Legal & Judiciary": {
        "api_category": "politics",
        "keywords": ["court", "verdict", "trial", "judge", "supreme court", "high court", "lawsuit", "judicial", "amendment", "constitution"]
    },
    "Defense & National Security": {
        "api_category": "world",
        "keywords": ["military", "army", "defense", "border", "geopolitical", "national security", "weapons", "warfare", "navy", "airforce", "procurement"]
    },
    "International & World News": {
        "api_category": "world",
        "keywords": ["global", "foreign policy", "diplomacy", "international", "conflict", "summit", "treaty", "world news"]
    },
    "Business & Corporate": {
        "api_category": "business",
        "keywords": ["corporate", "company", "merger", "startup", "acquisition", "board", "ceo", "revenue", "earnings"]
    },
    "Finance & Markets": {
        "api_category": "business",
        "keywords": ["stock", "market", "finance", "mutual fund", "commodity", "inflation", "central bank", "interest rate", "nifty", "sensex"]
    },
    "Economy & Trade": {
        "api_category": "business",
        "keywords": ["economy", "GDP", "trade", "budget", "tariff", "fiscal", "exports", "imports"]
    },
    "Technology & Software": {
        "api_category": "technology",
        "keywords": ["software", "gadget", "tech", "cybersecurity", "internet", "electronics", "app", "operating system"]
    },
    "Science & Space Exploration": {
        "api_category": "science",
        "keywords": ["space", "astronomy", "physics", "chemistry", "biology", "research", "nasa", "isro", "science", "mission"]
    },
    "Health & Medicine": {
        "api_category": "health",
        "keywords": ["health", "medicine", "healthcare", "epidemic", "pharma", "clinical", "disease", "vaccine", "doctor"]
    },
    "Education & Careers": {
        "api_category": None,
        "keywords": ["education", "exam", "university", "curriculum", "career", "admission", "school", "board exam", "student"]
    },
    "Environment & Climate Change": {
        "api_category": "environment",
        "keywords": ["climate", "green energy", "warming", "wildlife", "conservation", "pollution", "carbon", "environment"]
    },
    "Weather & Natural Disasters": {
        "api_category": "environment",
        "keywords": ["weather", "storm", "earthquake", "forecast", "rain", "flood", "cyclone", "disaster"]
    },
    "Infrastructure & Real Estate": {
        "api_category": "business",
        "keywords": ["infrastructure", "real estate", "highway", "transit", "metro", "property", "building", "construction"]
    },
    "Sports & Athletics": {
        "api_category": "sports",
        "keywords": ["sports", "match", "tournament", "league", "athlete", "player", "championship", "cricket", "football"]
    },
    "Entertainment & Cinema": {
        "api_category": "entertainment",
        "keywords": ["cinema", "movie", "film", "OTT", "actor", "release", "music", "song", "theater"]
    },
    "Pop Culture & Celebrity": {
        "api_category": "entertainment",
        "keywords": ["celebrity", "pop culture", "viral", "fashion", "showbiz", "influencer", "trend"]
    },
    "Lifestyle & Wellness": {
        "api_category": "health",
        "keywords": ["lifestyle", "wellness", "fitness", "diet", "nutrition", "mental health", "relationship", "yoga"]
    },
    "Travel & Tourism": {
        "api_category": "tourism",
        "keywords": ["travel", "tourism", "destination", "hotel", "resort", "flight", "aviation", "vacation"]
    },
    "Food & Culinary Arts": {
        "api_category": "food",
        "keywords": ["food", "culinary", "restaurant", "recipe", "chef", "cooking", "cuisine", "agriculture", "dining"]
    },
    "Human Interest & Profiles": {
        "api_category": None,
        "keywords": ["story", "profile", "community", "hero", "obituary", "inspiring", "feature story", "tribute"]
    },
    "Artificial Intelligence & Automation": {
        "api_category": "technology",
        "keywords": ["AI", "artificial intelligence", "LLM", "automation", "robot", "chip", "nvidia", "machine learning", "agentic"]
    }
}

# List of Country choices
COUNTRIES = {
    "Worldwide": "worldwide",
    "India (in)": "in",
    "United States (us)": "us",
    "United Kingdom (gb)": "gb",
    "Canada (ca)": "ca",
    "Australia (au)": "au",
    "Germany (de)": "de",
    "France (fr)": "fr",
    "Japan (jp)": "jp",
    "Singapore (sg)": "sg",
    "United Arab Emirates (ae)": "ae"
}

# Supported Translation & Narration Languages
AUDIO_LANGUAGES = {
    "English": "en",
    "Malayalam": "ml",
    "Tamil": "ta",
    "Hindi": "hi",
    "Kannada": "kn"
}

# Narrator Accents (Only for English)
ACCENTS = {
    "India (English)": "co.in",
    "United States (English)": "com",
    "United Kingdom (English)": "co.uk",
    "Canada (English)": "ca",
    "Australia (English)": "com.au"
}

# Initialize Session State
if "fetched_data" not in st.session_state:
    st.session_state["fetched_data"] = None
if "last_params" not in st.session_state:
    st.session_state["last_params"] = {}
if "using_outside_source" not in st.session_state:
    st.session_state["using_outside_source"] = False

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("🔑 Authentication & Params")

api_key = NEWSDATA_API_KEY
if not api_key or api_key == "YOUR_API_KEY_HERE":
    api_key = st.sidebar.text_input(
        label="NewsData.io API Key",
        type="password",
        help="Enter your API Key generated from NewsData.io dashboard."
    )

country_labels = list(COUNTRIES.keys())
default_country_index = country_labels.index("India (in)")
selected_country_label = st.sidebar.selectbox(
    label="Country",
    options=country_labels,
    index=default_country_index
)
country_code = COUNTRIES[selected_country_label]
country_name_clean = selected_country_label.split(" (")[0]

category_list = list(CUSTOM_CATEGORIES.keys())
selected_custom_category = st.sidebar.selectbox(
    label="Category",
    options=category_list,
    index=category_list.index("General")
)

query = st.sidebar.text_input(
    label="Query/Keyword Search",
    placeholder="e.g., Kerala, Maharashtra, AI"
)

max_articles = st.sidebar.slider(
    label="Max Articles to Display",
    min_value=10,
    max_value=50,
    value=20,
    step=10
)

selected_audio_lang_label = st.sidebar.selectbox(
    label="Podcast & Summary Language",
    options=list(AUDIO_LANGUAGES.keys()),
    index=0
)
audio_lang_code = AUDIO_LANGUAGES[selected_audio_lang_label]

accent_tld = "com"
if audio_lang_code == "en":
    selected_accent_label = st.sidebar.selectbox(
        label="English Accent",
        options=list(ACCENTS.keys()),
        index=0
    )
    accent_tld = ACCENTS[selected_accent_label]

# --- ADVANCED FILTERING OPTIONS ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Strict Filtering Rules")

strict_country = st.sidebar.checkbox(
    label="Strict Country Match",
    value=True
)

strict_category = st.sidebar.checkbox(
    label="Strict Category Match (Smart Keyword Filter)",
    value=True
)

auto_translate = st.sidebar.checkbox(
    label="Translate to Selected Language",
    value=True
)

# Fetch Button
fetch_button = st.sidebar.button(
    label="Fetch News Data",
    use_container_width=True,
    type="primary"
)

# Detect changes
current_params = {
    "api_key": api_key,
    "country_code": country_code,
    "category": selected_custom_category,
    "query": query,
    "max_articles": max_articles,
    "strict_country": strict_country,
    "strict_category": strict_category,
    "auto_translate": auto_translate,
    "language": audio_lang_code,
    "accent": accent_tld if audio_lang_code == "en" else "none"
}

params_changed = (
    st.session_state["fetched_data"] is not None and 
    st.session_state["last_params"] != current_params
)

if params_changed:
    st.sidebar.warning("⚠️ Parameters modified. Click 'Fetch News Data' to refresh results.")

# --- FETCH ACTION ---
if fetch_button:
    if not api_key or api_key == "YOUR_API_KEY_HERE" or not api_key.strip():
        st.error("⚠️ NewsData.io API Key is required. Please write your key at the top of app.py or enter it in the sidebar.")
    else:
        st.session_state["using_outside_source"] = False
        cat_info = CUSTOM_CATEGORIES[selected_custom_category]
        api_category = cat_info["api_category"]
        
        cat_keywords = cat_info["keywords"][:4]
        cat_query_string = " OR ".join(f'"{kw}"' if " " in kw else kw for kw in cat_keywords)
        
        if selected_custom_category == "General":
            if query.strip():
                final_q = query.strip()
            else:
                final_q = None
        else:
            if query.strip():
                final_q = f"({query.strip()}) AND ({cat_query_string})"
            else:
                final_q = cat_query_string
            
        params = {
            "apikey": api_key
        }
        if api_category:
            params["category"] = api_category
        if final_q:
            params["q"] = final_q
        if country_code != "worldwide":
            params["country"] = country_code
            
        api_url = "https://newsdata.io/api/1/news"
        
        with st.spinner("Fetching news articles..."):
            try:
                all_results = []
                next_page_token = None
                api_error_occurred = False
                
                while len(all_results) < max_articles:
                    current_params_query = params.copy()
                    if next_page_token:
                        current_params_query["page"] = next_page_token
                        
                    response = requests.get(api_url, params=current_params_query, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status")
                        
                        if status == "error":
                            error_info = data.get("results", {})
                            error_msg = error_info.get("message", "API returned error state.")
                            st.error(f"❌ API Error: {error_msg}")
                            api_error_occurred = True
                            break
                        
                        page_results = data.get("results", [])
                        if not page_results:
                            break
                            
                        all_results.extend(page_results)
                        next_page_token = data.get("nextPage")
                        
                        if not next_page_token:
                            break
                    else:
                        try:
                            err_json = response.json()
                            err_msg = err_json.get("results", {}).get("message", response.text)
                        except Exception:
                            err_msg = response.text
                        st.error(f"❌ API Request failed with status code {response.status_code}: {err_msg}")
                        api_error_occurred = True
                        break
                
                if not api_error_occurred:
                    st.session_state["fetched_data"] = {"status": "success", "results": all_results}
                    st.session_state["last_params"] = current_params.copy()
                    
            except requests.exceptions.RequestException as e:
                st.error(f"🔌 Connection/Request Error: {str(e)}")

# --- DISPLAY & FILTERING LOGIC ---
if st.session_state["fetched_data"] is not None:
    data = st.session_state["fetched_data"]
    
    raw_articles = data.get("results", [])
    seen_titles = set()
    
    main_articles = []
    mini_articles = []
    
    cat_keywords = CUSTOM_CATEGORIES[selected_custom_category]["keywords"]
    
    for article in raw_articles:
        title = article.get("title") or ""
        title_clean = title.strip()
        if not title_clean:
            continue
            
        if title_clean.lower() in [t.lower() for t in seen_titles] or is_similar_to_existing(title_clean, seen_titles, threshold=0.45):
            continue
            
        if strict_category and selected_custom_category != "General":
            title_text = (article.get("title") or "").lower()
            desc_text = (article.get("description") or "").lower()
            content_text = (article.get("content") or "").lower()
            
            keyword_match = False
            for kw in cat_keywords:
                if kw.lower() in title_text or kw.lower() in desc_text or kw.lower() in content_text:
                    keyword_match = True
                    break
            if not keyword_match:
                continue
                
        if strict_country and country_code != "worldwide":
            art_countries = [str(c).lower() for c in (article.get("country") or []) if c]
            if country_code not in art_countries:
                continue
                
        seen_titles.add(title_clean)
        
        desc = article.get("description")
        if not desc or not desc.strip() or desc.strip().lower() in ["no description provided.", "no description", "n/a"]:
            mini_articles.append(article)
        else:
            main_articles.append(article)
            
    # Fallback to Google News RSS
    if not main_articles and not mini_articles:
        st.session_state["using_outside_source"] = True
        rss_query = query.strip() if query.strip() else " OR ".join(cat_keywords[:3])
        if selected_custom_category == "General" and not query.strip():
            rss_query = "latest world news"
            
        with st.spinner("No results found on NewsData.io. Fetching from Google News RSS..."):
            raw_articles = fetch_google_news(rss_query, country_code, audio_lang_code)
            
        seen_titles = set()
        for article in raw_articles:
            title = article.get("title") or ""
            title_clean = title.strip()
            if not title_clean:
                continue
            if title_clean.lower() in [t.lower() for t in seen_titles] or is_similar_to_existing(title_clean, seen_titles, threshold=0.45):
                continue
            seen_titles.add(title_clean)
            
            desc = article.get("description")
            if not desc or not desc.strip() or desc.strip().lower() in ["no description provided.", "no description", "n/a"]:
                mini_articles.append(article)
            else:
                main_articles.append(article)
                
    # Dock & Rank
    scored_main = []
    for art in main_articles:
        score = calculate_article_score(art, query, cat_keywords)
        scored_main.append((score, art))
    scored_main.sort(key=lambda x: x[0], reverse=True)
    
    scored_mini = []
    for art in mini_articles:
        score = calculate_article_score(art, query, cat_keywords)
        scored_mini.append((score, art))
    scored_mini.sort(key=lambda x: x[0], reverse=True)
    
    final_main = [art for score, art in scored_main[:max_articles]]
    final_mini = [art for score, art in scored_mini[:max_articles - len(final_main)]]
    
    if not st.session_state["using_outside_source"]:
        with st.expander("Raw JSON Response", expanded=False):
            st.json(data)
            
    if not final_main and not final_mini:
        st.info("ℹ️ No articles found matching your criteria.")
    else:
        if st.session_state["using_outside_source"]:
            st.warning("⚡ Sourced from Google News feeds (no data found on NewsData.io).")
            
        processed_main = []
        processed_mini = []
        
        with st.spinner(f"Compiling and translating news summaries to {selected_audio_lang_label}..."):
            for idx, article in enumerate(final_main):
                title = article.get("title", "No Title Available")
                description = (article.get("description") or "")
                
                # Fetch sentiment
                sentiment = get_news_sentiment(title, description)
                
                if auto_translate:
                    title = translate_to_target_lang(title, audio_lang_code)
                    description = translate_to_target_lang(description, audio_lang_code)
                
                processed_main.append({
                    "title": title,
                    "summary": description,
                    "link": article.get("link", "#"),
                    "country": ", ".join(article.get("country", [])),
                    "source_id": article.get("source_id", "Unknown Source"),
                    "pub_date": article.get("pubDate", "Date not specified"),
                    "score": scored_main[idx][0],
                    "sentiment": sentiment
                })
                
            for idx, article in enumerate(final_mini):
                title = article.get("title", "No Title Available")
                if auto_translate:
                    title = translate_to_target_lang(title, audio_lang_code)
                
                processed_mini.append({
                    "title": title,
                    "link": article.get("link", "#"),
                    "source_id": article.get("source_id", "Unknown Source"),
                    "pub_date": article.get("pubDate", "Date not specified"),
                    "score": scored_mini[idx][0],
                    "sentiment": "Neutral"
                })

        # --- VIEW TABS (PODCAST & NEWS VS EDITORIAL NEWSLETTER) ---
        tab1, tab2 = st.tabs(["🎙️ Podcast Hub & News", "📰 Editorial Newsletter"])
        
        with tab1:
            # --- UNIFIED PODCAST SECTION ---
            st.markdown("## 🎙️ Podcast News Hub")
            
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"##### Continuous Podcast Playlist ({selected_audio_lang_label})")
                st.write(f"Generate a continuous modulated dual-host news briefing podcast covering all your selected articles in {selected_audio_lang_label}.")
                
                # Button to trigger full podcast script compilation
                if st.button("🎧 Generate Podcast Briefing", type="primary", use_container_width=True):
                    # Compile segments for alternating voices
                    audio_segments = []
                    
                    if audio_lang_code == "ml":
                        intro = f"നമസ്കാരം, {selected_custom_category} വാർത്താ പോഡ്‌കാസ്റ്റിലേക്ക് സ്വാഗതം. ഇന്നത്തെ പ്രധാന വാർത്തകൾ ഇതാ. "
                        outro = "വാർത്തകൾ അവസാനിച്ചു. ശ്രവിച്ചതിന് നന്ദി."
                    elif audio_lang_code == "ta":
                        intro = f"வணக்கம், {selected_custom_category} செய்திகள் பாட்காஸ்டிற்கு உங்களை வரவேற்கிறோம். இன்றைய முக்கிய செய்திகள் இதೋ. "
                        outro = "செய்திகள் நிறைவடைந்தது. கேட்டதற்கு நன்றி."
                    elif audio_lang_code == "hi":
                        intro = f"नमस्कार, {selected_custom_category} समाचार पॉडकास्ट में आपका स्वागत है। आज के मुख्य समाचार इस प्रकार हैं। "
                        outro = "समाचार समाप्त हुए। सुनने के लिए धन्यवाद।"
                    elif audio_lang_code == "kn":
                        intro = f"ನಮಸ್ಕಾರ, {selected_custom_category} ಸುದ್ದಿ ಪಾಡ್‌ಕಾಸ್ಟ್‌ಗೆ ಸ್ವಾಗತ. ಇಂದಿನ ಪ್ರಮುಖ ಸುದ್ದಿಗಳು ಇಲ್ಲಿವೆ. "
                        outro = "ಸುದ್ದಿಗಳು ಮುಗಿದವು. ಕೇಳಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು."
                    else:
                        intro = f"Welcome to your daily news briefing podcast on {selected_custom_category}. Here is the summary of the latest events. "
                        outro = "That concludes your news podcast update. Thank you for listening."
                    
                    audio_segments.append((intro, 0))
                    
                    for idx, art in enumerate(processed_main):
                        host_num = idx % 2 # Alternate Host 0 and Host 1
                        if audio_lang_code in ["ml", "ta", "hi", "kn"]:
                            body = f"വാർത്ത {idx + 1}. {art['title']}. {art['summary']}. "
                        else:
                            body = f"Story number {idx + 1}. {art['title']}. {art['summary']}. "
                        audio_segments.append((body, host_num))
                        
                    if processed_mini:
                        if audio_lang_code == "ml":
                            bullet_intro = "മറ്റ് പ്രധാന വിവരങ്ങൾ ചുരുക്കത്തിൽ ഇതാ. "
                        elif audio_lang_code == "ta":
                            bullet_intro = "இதர செய்திகள் சுருக்கமாக இதோ. "
                        elif audio_lang_code == "hi":
                            bullet_intro = "अन्य समाचार संक्षेप में। "
                        elif audio_lang_code == "kn":
                            bullet_intro = "ಇತರ ಸುದ್ದಿಗಳು ಸಂಕ್ಷಿಪ್ತವಾಗಿ ಇಲ್ಲಿವೆ. "
                        else:
                            bullet_intro = "Here are some quick bullet updates. "
                        audio_segments.append((bullet_intro, 0))
                        
                        for idx, art in enumerate(processed_mini):
                            host_num = idx % 2
                            audio_segments.append((art['title'] + ". ", host_num))
                            
                    audio_segments.append((outro, 0))
                    
                    with st.spinner(f"Generating modulated podcast audio in {selected_audio_lang_label}..."):
                        audio_file = generate_dual_host_audio(audio_segments, lang_code=audio_lang_code, accent_tld=accent_tld)
                        if audio_file:
                            st.audio(audio_file, format="audio/mp3", autoplay=True)
                            st.success("🎧 Podcast generated successfully! Play or download it below.")
                            
                            # Podcast Download button
                            st.download_button(
                                label="💾 Download Podcast MP3",
                                data=audio_file,
                                file_name=f"podcast_{selected_custom_category}_{datetime.now().strftime('%Y%m%d')}.mp3",
                                mime="audio/mp3",
                                use_container_width=True
                            )
                            
            with col2:
                # --- SENTIMENT DASHBOARD CHART ---
                sentiments = [art['sentiment'] for art in processed_main] + [art['sentiment'] for art in processed_mini]
                pos_count = sentiments.count("Positive")
                neg_count = sentiments.count("Negative")
                neu_count = sentiments.count("Neutral")
                
                st.markdown("##### 📊 Daily News Sentiment Profile")
                chart_data = {
                    "Positive 🙂": pos_count,
                    "Neutral 😐": neu_count,
                    "Negative 🙁": neg_count
                }
                st.bar_chart(chart_data)
                
            st.markdown("---")
            
            # Display Main News Cards
            if processed_main:
                st.markdown(f"### 📰 Featured Stories under **{selected_custom_category}** (Ranked by Relevancy & Date)")
                for art in processed_main:
                    source_display = art['source_id']
                    is_trusted_label = False
                    for ts in TRUSTED_SOURCE_SUBSTRINGS:
                        if ts in art['source_id'].lower():
                            is_trusted_label = True
                            break
                    
                    trusted_badge = '<span class="badge" style="background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71;">⭐ Trusted Source</span>' if is_trusted_label else ''
                    
                    # Sentiment badge
                    if art['sentiment'] == "Positive":
                        sent_badge = '<span class="badge" style="background-color: rgba(46, 204, 113, 0.15); color: #2ecc71;">🙂 Positive</span>'
                    elif art['sentiment'] == "Negative":
                        sent_badge = '<span class="badge" style="background-color: rgba(231, 76, 60, 0.15); color: #e74c3c;">🙁 Negative</span>'
                    else:
                        sent_badge = '<span class="badge" style="background-color: rgba(149, 165, 166, 0.15); color: #95a5a6;">😐 Neutral</span>'
                    
                    card_html = f"""<div class="article-card">
<div class="article-title"><a href="{art['link']}" target="_blank">{art['title']}</a></div>
<div class="meta-container">
<span class="badge badge-category">{selected_custom_category}</span>
<span class="badge badge-country">Country: {art['country']}</span>
<span class="badge badge-source">Source: {source_display}</span>
{trusted_badge}
{sent_badge}
<span class="badge badge-score">🔥 Match Score: {art['score']}</span>
</div>
<div class="description-text" style="font-size: 0.98rem; margin-bottom: 0.8rem; font-style: italic; border-left: 2px solid #FF4B4B; padding-left: 8px;">
{art['summary']}
</div>
<div class="article-date">📅 Published: {art['pub_date']}</div>
</div>"""
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Individual audio player inside an expander
                    with st.expander(f"🔊 Listen in {selected_audio_lang_label}: {art['title'][:40]}...", expanded=False):
                        if st.button("Generate Audio", key=f"tts_{art['title'][:15]}_{art['pub_date']}"):
                            with st.spinner("Generating audio..."):
                                single_text = f"{art['title']}. {art['summary']}"
                                single_audio = generate_audio(single_text, lang=audio_lang_code, tld=accent_tld)
                                if single_audio:
                                    st.audio(single_audio, format="audio/mp3", autoplay=True)

            # Display Mini Bulletins (Without descriptions)
            if processed_mini:
                st.markdown("---")
                st.markdown("### ⚡ Mini News Bulletins (Quick Updates)")
                
                for art in processed_mini:
                    st.markdown(f"""<div style="padding: 0.75rem 1rem; border-left: 3px solid #6c5ce7; background: rgba(108, 92, 231, 0.05); margin-bottom: 0.75rem; border-radius: 0 8px 8px 0;">
<strong style="font-size: 1.05rem;"><a href="{art['link']}" target="_blank" style="color: inherit; text-decoration: none;">{art['title']}</a></strong>
<div style="font-size: 0.8rem; margin-top: 0.3rem; color: #7f8c8d;">
Source: <b>{art['source_id']}</b> | Published: {art['pub_date']} | Match Score: <b>{art['score']}</b>
</div>
</div>""", unsafe_allow_html=True)
                    
                    with st.expander(f"🔊 Listen to Bulletin: {art['title'][:35]}...", expanded=False):
                        if st.button("Generate Bulletin Audio", key=f"tts_mini_{art['title'][:15]}_{art['pub_date']}"):
                            with st.spinner("Generating audio..."):
                                single_audio = generate_audio(art['title'], lang=audio_lang_code, tld=accent_tld)
                                if single_audio:
                                    st.audio(single_audio, format="audio/mp3", autoplay=True)

        with tab2:
            # --- EDITORIAL NEWSLETTER TAB ---
            st.markdown("## 📰 Morning Briefing Editorial Newsletter")
            st.write(f"Read or download a clean, structured text digest of the latest news in **{selected_audio_lang_label}**.")
            
            # Build Newsletter Text String
            newsletter_str = f"# DAILY EDITORIAL BRIEFING - {selected_custom_category.upper()}\n"
            newsletter_str += f"Date: {datetime.now().strftime('%Y-%m-%d')} | Target Edition: {country_name_clean}\n"
            newsletter_str += "="*60 + "\n\n"
            
            if processed_main:
                newsletter_str += "## FEATURED TOP STORIES\n\n"
                for idx, art in enumerate(processed_main):
                    newsletter_str += f"{idx+1}. {art['title']}\n"
                    newsletter_str += f"Source: {art['source_id']} | Date: {art['pub_date']}\n"
                    newsletter_str += f"Summary: {art['summary']}\n"
                    newsletter_str += f"Link: {art['link']}\n"
                    newsletter_str += "-"*40 + "\n\n"
                    
            if processed_mini:
                newsletter_str += "## QUICK BULLETINS\n\n"
                for art in processed_mini:
                    newsletter_str += f"• {art['title']} (Source: {art['source_id']})\n"
                    newsletter_str += f"  Link: {art['link']}\n\n"
                    
            # Render Newsletter on Screen inside code box for copying
            st.text_area(label="Newsletter Content (Markdown format)", value=newsletter_str, height=450)
            
            # Download Button
            st.download_button(
                label="📥 Download Newsletter Document (.txt)",
                data=newsletter_str,
                file_name=f"newsletter_{selected_custom_category}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
else:
    # Initial state helper message
    st.info("👈 Configure your parameters, then click **Fetch News Data** to test.")
