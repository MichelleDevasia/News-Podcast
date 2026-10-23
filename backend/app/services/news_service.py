"""
News Retrieval, RSS Parsing, Scoring, and Filtering Service.
Faithfully extracted from app.py without modifying weights, rankings, or filters.
"""

from datetime import datetime
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Any, Optional

import requests

from backend.app.core.constants import (
    TRUSTED_SOURCE_SUBSTRINGS,
    CUSTOM_CATEGORIES,
)
from backend.app.services.nlp_service import is_similar_to_existing


def parse_date(date_str: str) -> datetime:
    """
    Parses datetime strings in standard format or ISO 8601 format.
    Returns datetime.min if unparseable.
    """
    if not date_str:
        return datetime.min
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.min


def calculate_article_score(article: Dict[str, Any], user_query: Optional[str], cat_keywords: List[str]) -> float:
    """
    Composite scoring function to rank articles by:
    1. Trusted Source Boost (+45.0)
    2. User Query match (+20.0 title, +7.0 description, +3.0 content)
    3. Category Keywords match (+10.0 title, +4.0 description)
    4. Recency Freshness Boost (30.0 / (1.0 + elapsed_hours / 12.0))
    """
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
    for kw in (cat_keywords or []):
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


def fetch_google_news(query_text: str, country_code: str, lang_code: str = "en") -> List[Dict[str, Any]]:
    """
    Google News RSS Fetcher used as an outside source fallback when primary API yields no results.
    """
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


def fetch_newsdata(
    api_key: str,
    category: str = "General",
    query: Optional[str] = None,
    country_code: str = "worldwide",
    max_articles: int = 20
) -> Dict[str, Any]:
    """
    Fetches articles from NewsData.io API with automatic pagination up to max_articles.
    Returns standard dictionary with 'status' and 'results'.
    Raises RuntimeError on API errors or request exceptions.
    """
    if not api_key or not api_key.strip():
        raise ValueError("NewsData.io API key is required.")

    cat_info = CUSTOM_CATEGORIES.get(category, CUSTOM_CATEGORIES["General"])
    api_category = cat_info["api_category"]

    cat_keywords = cat_info["keywords"][:4]
    cat_query_string = " OR ".join(f'"{kw}"' if " " in kw else kw for kw in cat_keywords)

    query_str = (query or "").strip()
    if category == "General":
        final_q = query_str if query_str else None
    else:
        if query_str:
            final_q = f"({query_str}) AND ({cat_query_string})"
        else:
            final_q = cat_query_string

    params: Dict[str, Any] = {"apikey": api_key}
    if api_category:
        params["category"] = api_category
    if final_q:
        params["q"] = final_q
    if country_code and country_code != "worldwide":
        params["country"] = country_code

    api_url = "https://newsdata.io/api/1/news"
    all_results: List[Dict[str, Any]] = []
    next_page_token: Optional[str] = None

    while len(all_results) < max_articles:
        current_params_query = params.copy()
        if next_page_token:
            current_params_query["page"] = next_page_token

        response = requests.get(api_url, params=current_params_query, timeout=15)

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status == "error":
                error_msg = data.get("results", {}).get("message", "API returned error state.")
                raise RuntimeError(f"NewsData.io Error: {error_msg}")

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
            raise RuntimeError(f"NewsData.io Request failed ({response.status_code}): {err_msg}")

    return {"status": "success", "results": all_results}


def filter_and_rank_articles(
    raw_articles: List[Dict[str, Any]],
    category: str = "General",
    country_code: str = "worldwide",
    query: str = "",
    max_articles: int = 20,
    strict_country: bool = True,
    strict_category: bool = True,
    audio_lang_code: str = "en"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool]:
    """
    Applies deduplication, strict category keywords filtering, strict country matching,
    Google News RSS fallback if empty, and relevance scoring.
    Returns (final_main, final_mini, used_fallback).
    """
    cat_info = CUSTOM_CATEGORIES.get(category, CUSTOM_CATEGORIES["General"])
    cat_keywords = cat_info["keywords"]

    seen_titles: set = set()
    main_articles: List[Dict[str, Any]] = []
    mini_articles: List[Dict[str, Any]] = []

    for article in raw_articles:
        title = article.get("title") or ""
        title_clean = title.strip()
        if not title_clean:
            continue

        if title_clean.lower() in [t.lower() for t in seen_titles] or is_similar_to_existing(title_clean, seen_titles, threshold=0.45):
            continue

        if strict_category and category != "General":
            title_text = (article.get("title") or "").lower()
            desc_text = (article.get("description") or "").lower()
            content_text = (article.get("content") or "").lower()

            keyword_match = any(
                kw.lower() in title_text or kw.lower() in desc_text or kw.lower() in content_text
                for kw in cat_keywords
            )
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

    used_fallback = False
    # Fallback to Google News RSS if no articles matched
    if not main_articles and not mini_articles:
        used_fallback = True
        query_clean = query.strip()
        rss_query = query_clean if query_clean else " OR ".join(cat_keywords[:3])
        if category == "General" and not query_clean:
            rss_query = "latest world news"

        raw_fallback = fetch_google_news(rss_query, country_code, audio_lang_code)
        seen_titles = set()
        for article in raw_fallback:
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

    # Attach score to article dictionaries
    for score, art in scored_main:
        art["score"] = score
    for score, art in scored_mini:
        art["score"] = score

    final_main = [art for score, art in scored_main[:max_articles]]
    final_mini = [art for score, art in scored_mini[:max_articles - len(final_main)]]

    return final_main, final_mini, used_fallback
