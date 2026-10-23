/**
 * Reusable API helper for frontend HTTP requests.
 * Uses the Vite '/api' reverse proxy path to reach the backend seamlessly.
 */

import type { OptionsResponse } from '../types/options';
import type { NewsRequest, NewsResponse, PodcastRequest } from '../types/news';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Checks backend health status from /api/health.
 */
export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health', {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new ApiError(`Health check failed (${response.status})`, response.status);
  }

  return response.json();
}

/**
 * Fetches available categories, countries, languages, and accents from the backend.
 */
export async function getOptions(): Promise<OptionsResponse> {
  const response = await fetch('/api/options', {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let detailMessage = response.statusText;
    try {
      const errorJson = await response.json();
      detailMessage = errorJson.detail || detailMessage;
    } catch {
      // Fallback
    }
    throw new ApiError(`Failed to load options: ${detailMessage}`, response.status);
  }

  return response.json();
}

/**
 * Retrieves and filters real news articles from POST /api/news.
 */
export async function fetchNews(request: NewsRequest): Promise<NewsResponse> {
  const response = await fetch('/api/news', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let detailMessage = response.statusText;
    try {
      const errorJson = await response.json();
      detailMessage = errorJson.detail || detailMessage;
    } catch {
      // Fallback
    }
    throw new ApiError(`News retrieval failed: ${detailMessage}`, response.status);
  }

  return response.json();
}

/**
 * Synthesizes a dual-host audio podcast from POST /api/podcast.
 * Returns the raw binary MP3 Blob for in-memory browser playback.
 */
export async function generatePodcastAudio(request: PodcastRequest): Promise<Blob> {
  const response = await fetch('/api/podcast', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'audio/mpeg',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let detailMessage = response.statusText;
    try {
      const errorJson = await response.json();
      detailMessage = errorJson.detail || detailMessage;
    } catch {
      // Fallback
    }
    throw new ApiError(`Audio generation failed: ${detailMessage}`, response.status);
  }

  return response.blob();
}
