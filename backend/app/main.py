"""
FastAPI application for the News Podcast backend.
Provides endpoints for configuration options, news retrieval & ranking, and podcast audio generation.
"""

import io
import logging
import os
from typing import Dict, List, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.core.constants import (
    CUSTOM_CATEGORIES,
    COUNTRIES,
    AUDIO_LANGUAGES,
    ACCENTS,
)
from backend.app.schemas.news import (
    OptionItem,
    AccentItem,
    OptionsResponse,
    NewsRequest,
    NewsResponse,
    ArticleItem,
    MiniArticleItem,
    SentimentSummary,
    PodcastRequest,
)
from backend.app.services.nlp_service import (
    translate_to_target_lang,
    get_news_sentiment,
)
from backend.app.services.news_service import (
    fetch_newsdata,
    fetch_google_news,
    filter_and_rank_articles,
)
from backend.app.services.audio_service import (
    build_podcast_segments,
    generate_dual_host_audio,
)

# Load environment variables from .env file if present
load_dotenv()
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "").strip()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="News Podcast API",
    description="Backend REST API powering personalized news briefs and dual-host podcast audio generation.",
    version="0.1.0"
)

# Configure CORS for local React development
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_newsdata_api_key() -> str:
    """
    Returns the NewsData.io API key from environment configuration.
    """
    return os.getenv("NEWSDATA_API_KEY", "").strip()


@app.get("/api/health", tags=["System"])
def health_check():
    """
    Health check endpoint returning the status of the backend API.
    """
    return {
        "status": "healthy",
        "service": "news-podcast-backend",
        "version": "0.1.0"
    }


@app.get("/", tags=["System"])
def root():
    """
    Root endpoint directing users to the API documentation.
    """
    return {
        "message": "News Podcast API is running. Visit /docs for interactive Swagger API documentation."
    }


@app.get("/api/options", response_model=OptionsResponse, tags=["Configuration"])
def get_options():
    """
    Returns available news categories, supported countries, audio languages, and narrator accents.
    Preserves exact option values and labels from the application constants.
    """
    categories = list(CUSTOM_CATEGORIES.keys())

    countries = [
        OptionItem(label=label, code=code)
        for label, code in COUNTRIES.items()
    ]

    languages = [
        OptionItem(label=label, code=code)
        for label, code in AUDIO_LANGUAGES.items()
    ]

    accents = [
        AccentItem(label=label, tld=tld)
        for label, tld in ACCENTS.items()
    ]

    return OptionsResponse(
        categories=categories,
        countries=countries,
        languages=languages,
        accents=accents
    )


@app.post("/api/news", response_model=NewsResponse, tags=["News"])
def get_news(request: NewsRequest):
    """
    Retrieves, deduplicates, scores, and optionally translates news articles matching user criteria.
    Falls back gracefully to Google News RSS if NewsData.io credentials are unavailable or return empty/error states.
    """
    # 1. Validate Category
    if request.category not in CUSTOM_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported category '{request.category}'. Must be one of: {list(CUSTOM_CATEGORIES.keys())}"
        )

    # 2. Validate Country
    valid_country_codes = set(COUNTRIES.values())
    if request.country not in valid_country_codes:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported country code '{request.country}'. Must be one of: {list(valid_country_codes)}"
        )

    # 3. Validate Language
    valid_lang_codes = set(AUDIO_LANGUAGES.values())
    if request.language not in valid_lang_codes:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported language code '{request.language}'. Must be one of: {list(valid_lang_codes)}"
        )

    raw_articles: List[Dict[str, Any]] = []
    source_used = "newsdata"
    api_key = get_newsdata_api_key()

    # 4. Attempt Primary Fetch (NewsData.io) if API key is configured
    if api_key:
        try:
            data = fetch_newsdata(
                api_key=api_key,
                category=request.category,
                query=request.query,
                country_code=request.country,
                max_articles=request.max_articles
            )
            raw_articles = data.get("results", [])
        except Exception as e:
            logger.warning(f"NewsData.io fetch failed, switching to RSS fallback: {e}")
            raw_articles = []
    else:
        logger.info("NEWSDATA_API_KEY not configured; using Google News RSS fallback.")

    # 5. Filter, Deduplicate, Fallback, and Rank
    final_main, final_mini, used_fallback = filter_and_rank_articles(
        raw_articles=raw_articles,
        category=request.category,
        country_code=request.country,
        query=request.query or "",
        max_articles=request.max_articles,
        strict_country=request.strict_country,
        strict_category=request.strict_category,
        audio_lang_code=request.language
    )

    if used_fallback or not api_key:
        source_used = "google_news_rss"

    # 6. Process & Enrich Main Articles (Sentiment, Translation, Formatting)
    processed_main: List[ArticleItem] = []
    for art in final_main:
        title = art.get("title", "No Title Available")
        description = art.get("description") or ""

        # Calculate sentiment on original text
        sentiment = get_news_sentiment(title, description)

        # Translate if requested
        if request.auto_translate and request.language != "en":
            title = translate_to_target_lang(title, request.language)
            description = translate_to_target_lang(description, request.language)

        countries_val = art.get("country", [])
        country_str = ", ".join(countries_val) if isinstance(countries_val, list) else str(countries_val)

        processed_main.append(ArticleItem(
            title=title,
            summary=description,
            link=art.get("link", "#"),
            country=country_str or request.country,
            source_id=art.get("source_id", "Unknown Source"),
            pub_date=art.get("pubDate", "Date not specified"),
            score=art.get("score", 0.0),
            sentiment=sentiment
        ))

    # 7. Process & Enrich Mini Bulletins
    processed_mini: List[MiniArticleItem] = []
    for art in final_mini:
        title = art.get("title", "No Title Available")
        if request.auto_translate and request.language != "en":
            title = translate_to_target_lang(title, request.language)

        processed_mini.append(MiniArticleItem(
            title=title,
            link=art.get("link", "#"),
            source_id=art.get("source_id", "Unknown Source"),
            pub_date=art.get("pubDate", "Date not specified"),
            score=art.get("score", 0.0),
            sentiment="Neutral"
        ))

    # 8. Compute Sentiment Profile
    all_sentiments = [a.sentiment for a in processed_main] + [a.sentiment for a in processed_mini]
    sentiment_summary = SentimentSummary(
        positive=all_sentiments.count("Positive"),
        neutral=all_sentiments.count("Neutral"),
        negative=all_sentiments.count("Negative")
    )

    return NewsResponse(
        status="success",
        source=source_used,
        category=request.category,
        country=request.country,
        language=request.language,
        total_main=len(processed_main),
        total_mini=len(processed_mini),
        main_articles=processed_main,
        mini_articles=processed_mini,
        sentiment_summary=sentiment_summary
    )


@app.post("/api/podcast", tags=["Podcast"])
def generate_podcast(request: PodcastRequest):
    """
    Generates a dual-host modulated MP3 audio briefing for the supplied articles.
    Returns in-memory audio/mpeg binary stream.
    """
    # 1. Validate Language
    valid_lang_codes = set(AUDIO_LANGUAGES.values())
    if request.language not in valid_lang_codes:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported audio language '{request.language}'. Must be one of: {list(valid_lang_codes)}"
        )

    # 2. Validate Accent
    valid_accents = set(ACCENTS.values())
    if request.accent not in valid_accents:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported accent '{request.accent}'. Must be one of: {list(valid_accents)}"
        )

    # 3. Ensure Articles are Provided
    if not request.main_articles and not request.mini_articles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one article (main or mini) is required to synthesize a podcast."
        )

    # 4. Convert Pydantic payloads to dictionaries for audio_service
    main_dicts = [
        {"title": a.title, "summary": a.summary or ""}
        for a in request.main_articles
    ]
    mini_dicts = [
        {"title": a.title}
        for a in request.mini_articles
    ]

    # 5. Build Script Segments (Host 0 and Host 1 alternation)
    segments = build_podcast_segments(
        main_articles=main_dicts,
        mini_articles=mini_dicts,
        category=request.category,
        audio_lang_code=request.language
    )

    # 6. Synthesize Dual-Host Audio
    audio_buffer = generate_dual_host_audio(
        segments=segments,
        lang_code=request.language,
        accent_tld=request.accent
    )

    if not audio_buffer or len(audio_buffer.getvalue()) == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to synthesize podcast audio. Text-to-speech service may be temporarily unavailable."
        )

    # Safe filename for Content-Disposition
    clean_cat = "".join(c for c in request.category if c.isalnum() or c in ("_", "-")).lower() or "news"
    filename = f"podcast_{clean_cat}_{request.language}.mp3"

    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    )
