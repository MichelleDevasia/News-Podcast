"""
Pydantic schemas for News and Podcast API endpoints.
Validates input constraints, supported languages/categories, and formats responses.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


# --- Options Models ---
class OptionItem(BaseModel):
    label: str
    code: str

class AccentItem(BaseModel):
    label: str
    tld: str

class OptionsResponse(BaseModel):
    categories: List[str]
    countries: List[OptionItem]
    languages: List[OptionItem]
    accents: List[AccentItem]


# --- News Models ---
class NewsRequest(BaseModel):
    country: str = Field(
        default="in",
        description="Country code (e.g. 'in', 'us', 'gb', 'worldwide')"
    )
    category: str = Field(
        default="General",
        description="News category name matching CUSTOM_CATEGORIES"
    )
    query: Optional[str] = Field(
        default="",
        max_length=200,
        description="Optional keyword search string"
    )
    max_articles: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Maximum articles to return (between 1 and 50)"
    )
    language: str = Field(
        default="en",
        description="Output language code ('en', 'ml', 'ta', 'hi', 'kn')"
    )
    strict_country: bool = Field(
        default=True,
        description="Strictly match the specified country"
    )
    strict_category: bool = Field(
        default=True,
        description="Strictly filter by category keywords"
    )
    auto_translate: bool = Field(
        default=True,
        description="Translate titles and summaries to the target language"
    )


class ArticleItem(BaseModel):
    title: str
    summary: str
    link: str
    country: str
    source_id: str
    pub_date: str
    score: float
    sentiment: str


class MiniArticleItem(BaseModel):
    title: str
    link: str
    source_id: str
    pub_date: str
    score: float
    sentiment: str


class SentimentSummary(BaseModel):
    positive: int
    neutral: int
    negative: int


class NewsResponse(BaseModel):
    status: str
    source: str
    category: str
    country: str
    language: str
    total_main: int
    total_mini: int
    main_articles: List[ArticleItem]
    mini_articles: List[MiniArticleItem]
    sentiment_summary: SentimentSummary


# --- Podcast Models ---
class ArticlePayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = Field(default="", max_length=2500)


class MiniArticlePayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class PodcastRequest(BaseModel):
    category: str = Field(
        default="General",
        max_length=100,
        description="Category name for podcast intro and title"
    )
    language: str = Field(
        default="en",
        description="Audio language code ('en', 'ml', 'ta', 'hi', 'kn')"
    )
    accent: str = Field(
        default="com",
        description="Accent TLD for English voice modulation ('com', 'co.in', 'co.uk', 'ca', 'com.au')"
    )
    main_articles: List[ArticlePayload] = Field(
        default_factory=list,
        max_length=30,
        description="Main featured stories with summaries"
    )
    mini_articles: List[MiniArticlePayload] = Field(
        default_factory=list,
        max_length=20,
        description="Quick bullet updates without summaries"
    )
