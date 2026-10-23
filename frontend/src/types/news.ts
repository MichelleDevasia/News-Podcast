/**
 * TypeScript types for News retrieval and Podcast generation.
 * Maps 1:1 with the FastAPI backend schemas in backend/app/schemas/news.py.
 */

export interface ArticleItem {
  title: string;
  summary: string;
  link: string;
  country: string;
  source_id: string;
  pub_date: string;
  score: number;
  sentiment: string;
}

export interface MiniArticleItem {
  title: string;
  link: string;
  source_id: string;
  pub_date: string;
  score: number;
  sentiment: string;
}

export interface SentimentSummary {
  positive: number;
  neutral: number;
  negative: number;
}

export interface NewsResponse {
  status: string;
  source: string;
  category: string;
  country: string;
  language: string;
  total_main: number;
  total_mini: number;
  main_articles: ArticleItem[];
  mini_articles: MiniArticleItem[];
  sentiment_summary: SentimentSummary;
}

export interface NewsRequest {
  country: string;
  category: string;
  query?: string;
  max_articles: number;
  language: string;
  strict_country?: boolean;
  strict_category?: boolean;
  auto_translate?: boolean;
}

export interface ArticlePayload {
  title: string;
  summary?: string;
}

export interface MiniArticlePayload {
  title: string;
}

export interface PodcastRequest {
  category: string;
  language: string;
  accent: string;
  main_articles: ArticlePayload[];
  mini_articles: MiniArticlePayload[];
}
