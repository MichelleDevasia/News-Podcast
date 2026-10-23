"""
Shared domain constants, category mappings, and language configurations.
Extracted from app.py faithfully without altering weights, keywords, or mappings.
"""

# List of trusted source patterns to boost in article scoring (+45.0 points)
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

# Supported Country choices
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
