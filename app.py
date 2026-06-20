import streamlit as st
import requests
from deep_translator import GoogleTranslator
from datetime import datetime
import io
import re
from gtts import gTTS

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
</style>
""", unsafe_allow_html=True)

# Helper function to translate text to a target language
def translate_to_target_lang(text, target_lang):
    if not text or not text.strip():
        return text
    try:
        # For English, only translate if it contains non-ASCII characters to save speed
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


# High-density AI summarization using Gemini 1.5 Flash via REST API
def gemini_summarize(article_title, description, content, gemini_api_key):
    # Fallback to local summary if Gemini Key is not provided
    if not gemini_api_key or not gemini_api_key.strip():
        return local_summarize_fallback(article_title, description, content)
        
    full_text = f"Title: {article_title}\nDescription: {description}\nContent: {content}"
    prompt = f"Ingest the following news article and compress it into a simple, concise 2-to-3 sentence summary. Keep it factual and brief.\n\nNews Data:\n{full_text}"
    model = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key.strip()}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            res_json = response.json()
            summary_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return summary_text.strip()
    except Exception:
        pass
        
    return local_summarize_fallback(article_title, description, content)

# Fallback method parsing text using local rules
def local_summarize_fallback(title, description, content):
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

# TTS Audio Generation Helper
def generate_audio(text, lang='en', tld='com'):
    try:
        # Only use tld for English regional accents
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

# Composite scoring function to rank article by Importance + Recency
def calculate_article_score(article, user_query, cat_keywords):
    score = 0.0
    title = (article.get("title") or "").lower()
    description = (article.get("description") or "").lower()
    content = (article.get("content") or "").lower()
    
    # 1. Importance matching (User Query)
    if user_query:
        uq = user_query.lower()
        if uq in title:
            score += 20.0
        elif uq in description:
            score += 7.0
        elif uq in content:
            score += 3.0
            
    # 2. Importance matching (Category Keywords)
    for kw in cat_keywords:
        kw_l = kw.lower()
        if kw_l in title:
            score += 10.0
        elif kw_l in description:
            score += 4.0
            
    # 3. Recency Boost (Freshness)
    pub_date_str = article.get("pubDate")
    if pub_date_str:
        pub_dt = parse_date(pub_date_str)
        now = datetime.now()
        elapsed_hours = (now - pub_dt).total_seconds() / 3600.0
        if elapsed_hours < 0:
            elapsed_hours = 0
            
        # Give higher weight to younger news
        recency_score = 30.0 / (1.0 + (elapsed_hours / 12.0))
        score += recency_score
        
    return round(score, 1)

# Main Title Header
st.markdown("<h1 class='main-title'>🎙️ News Podcast & API Tester</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Convert matching news articles from NewsData.io into customizable podcast briefs.</p>", unsafe_allow_html=True)

# Mapping of custom user-friendly categories to NewsData.io API categories and keywords
CUSTOM_CATEGORIES = {
    "Politics & Governance": {
        "api_category": "politics",
        "keywords": ["politics", "election", "political party", "assembly", "policy", "government scheme", "minister", "parliament", "governance"]
    },
    "Crime & Public Safety": {
        "api_category": "general",
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
        "api_category": "general",
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
        "api_category": "general",
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

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("🔑 Authentication & Params")

api_key = st.sidebar.text_input(
    label="NewsData.io API Key",
    type="password",
    help="Enter your API Key generated from NewsData.io dashboard."
)

gemini_api_key = st.sidebar.text_input(
    label="Gemini API Key (Optional)",
    type="password",
    help="Enter Gemini API key to enable AI summarization. If omitted, local filters will run."
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
    index=category_list.index("Politics & Governance")
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

# Language Select box
selected_audio_lang_label = st.sidebar.selectbox(
    label="Podcast & Summary Language",
    options=list(AUDIO_LANGUAGES.keys()),
    index=0
)
audio_lang_code = AUDIO_LANGUAGES[selected_audio_lang_label]

# Narrator Accent (Only shows if English is selected)
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
    value=True,
    help="Automatically translate titles & descriptions to the selected podcast language."
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
    "gemini_api_key": gemini_api_key,
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
    if not api_key.strip():
        st.error("⚠️ NewsData.io API Key is required. Please enter it in the sidebar.")
    else:
        cat_info = CUSTOM_CATEGORIES[selected_custom_category]
        api_category = cat_info["api_category"]
        
        cat_keywords = cat_info["keywords"][:4]
        cat_query_string = " OR ".join(f'"{kw}"' if " " in kw else kw for kw in cat_keywords)
        
        if query.strip():
            final_q = f"({query.strip()}) AND ({cat_query_string})"
        else:
            final_q = cat_query_string
            
        params = {
            "apikey": api_key,
            "category": api_category,
            "q": final_q
        }
        
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
                
                if not api_error_occurred and all_results:
                    st.session_state["fetched_data"] = {"status": "success", "results": all_results}
                    st.session_state["last_params"] = current_params.copy()
                    st.success("🎉 Successfully fetched news data!")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"🔌 Connection/Request Error: {str(e)}")

# --- DISPLAY LOGIC ---
if st.session_state["fetched_data"] is not None:
    data = st.session_state["fetched_data"]
    
    # Show raw JSON response
    with st.expander("Raw JSON Response", expanded=False):
        st.json(data)
        
    # Process articles
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
            
        # Check for exact duplicate OR highly similar duplicate from other sources
        if title_clean.lower() in [t.lower() for t in seen_titles] or is_similar_to_existing(title_clean, seen_titles, threshold=0.45):
            continue
            
        if strict_category:
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
    
    if not final_main and not final_mini:
        st.info("ℹ️ No unique articles found matching your strict criteria. Try disabling 'Strict Country Match' or 'Strict Category Match'.")
    else:
        processed_main = []
        processed_mini = []
        
        with st.spinner(f"Compiling and translating news summaries to {selected_audio_lang_label}..."):
            for idx, article in enumerate(final_main):
                title = article.get("title", "No Title Available")
                description = (article.get("description") or "")
                content = (article.get("content") or "")
                
                # First summarize the raw text to 2-3 sentences
                summary_text = gemini_summarize(title, description, content, gemini_api_key)
                
                # Then translate both title and summary to target language
                if auto_translate:
                    title = translate_to_target_lang(title, audio_lang_code)
                    summary_text = translate_to_target_lang(summary_text, audio_lang_code)
                
                processed_main.append({
                    "title": title,
                    "summary": summary_text,
                    "link": article.get("link", "#"),
                    "country": ", ".join(article.get("country", [])),
                    "source_id": article.get("source_id", "Unknown Source"),
                    "pub_date": article.get("pubDate", "Date not specified"),
                    "score": scored_main[idx][0]
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
                    "score": scored_mini[idx][0]
                })

        # --- UNIFIED PODCAST SECTION ---
        st.markdown("## 🎙️ Podcast News Hub")
        
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown(f"##### Continuous Podcast Playlist ({selected_audio_lang_label})")
            st.write(f"Generate a continuous news briefing voice podcast covering all your selected articles in {selected_audio_lang_label}.")
            
            # Button to trigger full podcast script compilation
            if st.button("🎧 Generate Podcast Briefing", type="primary", use_container_width=True):
                # Build unified script in the target language (gTTS handles speech synthesis)
                if audio_lang_code == "ml":
                    intro = f"നമസ്കാരം, {selected_custom_category} വാർത്താ പോഡ്‌കാസ്റ്റിലേക്ക് സ്വാഗതം. ഇന്നത്തെ പ്രധാന വാർത്തകൾ ഇതാ. "
                    outro = "വാർത്തകൾ അവസാനിച്ചു. ശ്രവിച്ചതിന് നന്ദി."
                elif audio_lang_code == "ta":
                    intro = f"வணக்கம், {selected_custom_category} செய்திகள் பாட்காஸ்டிற்கு உங்களை வரவேற்கிறோம். இன்றைய முக்கிய செய்திகள் இதோ. "
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
                
                full_script = intro
                for idx, art in enumerate(processed_main):
                    if audio_lang_code in ["ml", "ta", "hi", "kn"]:
                        full_script += f"വാർത്ത {idx + 1}. {art['title']}. {art['summary']}. "
                    else:
                        full_script += f"Story number {idx + 1}. {art['title']}. {art['summary']}. "
                    
                if processed_mini:
                    if audio_lang_code == "ml":
                        full_script += "മറ്റ് പ്രധാന വിവരങ്ങൾ ചുരുക്കത്തിൽ ഇതാ. "
                    elif audio_lang_code == "ta":
                        full_script += "இதர செய்திகள் சுருக்கமாக இதோ. "
                    elif audio_lang_code == "hi":
                        full_script += "अन्य समाचार संक्षेप में। "
                    elif audio_lang_code == "kn":
                        full_script += "ಇತರ ಸುದ್ದಿಗಳು ಸಂಕ್ಷಿಪ್ತವಾಗಿ ಇಲ್ಲಿವೆ. "
                    else:
                        full_script += "Here are some quick bullet updates. "
                        
                    for art in processed_mini:
                        full_script += f"{art['title']}. "
                        
                full_script += outro
                
                with st.spinner(f"Generating unified podcast audio in {selected_audio_lang_label}..."):
                    audio_file = generate_audio(full_script, lang=audio_lang_code, tld=accent_tld)
                    if audio_file:
                        st.audio(audio_file, format="audio/mp3", autoplay=True)
                        st.success("🎧 Podcast generated successfully! Press play above.")
                        
        with col2:
            st.info(f"🎤 **Language:** {selected_audio_lang_label}\n\n"
                    f"📰 **Stats:** {len(processed_main)} main stories, {len(processed_mini)} mini bulletins ranked.")

        st.markdown("---")
        
        # Display Main News Cards
        if processed_main:
            st.markdown(f"### 📰 Featured Stories under **{selected_custom_category}** (Ranked by Relevancy & Date)")
            for art in processed_main:
                card_html = f"""
                <div class="article-card">
                    <div class="article-title"><a href="{art['link']}" target="_blank">{art['title']}</a></div>
                    <div class="meta-container">
                        <span class="badge badge-category">{selected_custom_category}</span>
                        <span class="badge badge-country">Country: {art['country']}</span>
                        <span class="badge badge-source">Source: {art['source_id']}</span>
                        <span class="badge badge-score">🔥 Match Score: {art['score']}</span>
                    </div>
                    <div style="font-size: 0.98rem; margin-bottom: 0.8rem; line-height: 1.5; font-style: italic; border-left: 2px solid #FF4B4B; padding-left: 8px;">
                        {art['summary']}
                    </div>
                    <div class="article-date">📅 Published: {art['pub_date']}</div>
                </div>
                """
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
                st.markdown(f"""
                <div style="padding: 0.75rem 1rem; border-left: 3px solid #6c5ce7; background: rgba(108, 92, 231, 0.05); margin-bottom: 0.75rem; border-radius: 0 8px 8px 0;">
                    <strong style="font-size: 1.05rem;"><a href="{art['link']}" target="_blank" style="color: inherit; text-decoration: none;">{art['title']}</a></strong>
                    <div style="font-size: 0.8rem; margin-top: 0.3rem; color: #7f8c8d;">
                        Source: <b>{art['source_id']}</b> | Published: {art['pub_date']} | Match Score: <b>{art['score']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Small individual player for bullet updates
                with st.expander(f"🔊 Listen to Bulletin: {art['title'][:35]}...", expanded=False):
                    if st.button("Generate Bulletin Audio", key=f"tts_mini_{art['title'][:15]}_{art['pub_date']}"):
                        with st.spinner("Generating audio..."):
                            single_audio = generate_audio(art['title'], lang=audio_lang_code, tld=accent_tld)
                            if single_audio:
                                st.audio(single_audio, format="audio/mp3", autoplay=True)
else:
    # Initial state helper message
    st.info("👈 Enter your API Keys in the sidebar and configure your parameters, then click **Fetch News Data** to test.")
