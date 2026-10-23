"""
Deterministic Unit & Integration Tests for FastAPI Endpoints.
Uses FastAPI TestClient with mocked external calls to verify:
- /api/health
- /api/options
- /api/news (success, validation error, upstream failure, fallback)
- /api/podcast (success, validation error, synthesis failure, MP3 headers)
"""

import io
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from backend.app.main import app


class TestEndpoints(unittest.TestCase):
    """Test suite for FastAPI endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # --- Health Endpoint Tests ---
    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "news-podcast-backend")

    # --- Options Endpoint Tests ---
    def test_options_endpoint(self):
        response = self.client.get("/api/options")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("categories", data)
        self.assertIn("countries", data)
        self.assertIn("languages", data)
        self.assertIn("accents", data)

        # Check that General category exists
        self.assertIn("General", data["categories"])

        # Check country list format
        country_codes = [c["code"] for c in data["countries"]]
        self.assertIn("in", country_codes)
        self.assertIn("us", country_codes)

        # Check languages
        lang_codes = [l["code"] for l in data["languages"]]
        self.assertIn("en", lang_codes)
        self.assertIn("ml", lang_codes)
        self.assertIn("ta", lang_codes)
        self.assertIn("hi", lang_codes)
        self.assertIn("kn", lang_codes)

    # --- News Endpoint Tests ---
    @patch("backend.app.main.get_newsdata_api_key", return_value="test_key")
    @patch("backend.app.main.fetch_newsdata")
    def test_news_endpoint_success(self, mock_fetch_newsdata, mock_api_key):
        # Title and description include category keywords ("tech", "software") to satisfy strict_category
        mock_fetch_newsdata.return_value = {
            "status": "success",
            "results": [
                {
                    "title": "Quantum computing tech milestone reached",
                    "description": "Researchers achieve breakthrough in new tech software for quantum hardware.",
                    "link": "https://example.com/quantum",
                    "country": ["in"],
                    "source_id": "BBC",
                    "pubDate": "2026-06-20 10:00:00"
                }
            ]
        }

        payload = {
            "country": "in",
            "category": "Technology & Software",
            "query": "quantum",
            "max_articles": 5,
            "language": "en",
            "strict_country": True,
            "strict_category": True,
            "auto_translate": False
        }

        response = self.client.post("/api/news", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["source"], "newsdata")
        self.assertEqual(data["total_main"], 1)
        self.assertEqual(data["main_articles"][0]["title"], "Quantum computing tech milestone reached")
        self.assertIn("sentiment_summary", data)

    def test_news_endpoint_invalid_category(self):
        payload = {
            "country": "in",
            "category": "NonExistentCategory123",
            "max_articles": 5,
            "language": "en"
        }
        response = self.client.post("/api/news", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unsupported category", response.json()["detail"])

    def test_news_endpoint_invalid_country(self):
        payload = {
            "country": "invalid_country_xyz",
            "category": "General",
            "max_articles": 5,
            "language": "en"
        }
        response = self.client.post("/api/news", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unsupported country code", response.json()["detail"])

    def test_news_endpoint_invalid_language(self):
        payload = {
            "country": "in",
            "category": "General",
            "max_articles": 5,
            "language": "klingon"
        }
        response = self.client.post("/api/news", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unsupported language code", response.json()["detail"])

    @patch("backend.app.main.get_newsdata_api_key", return_value="test_key")
    @patch("backend.app.main.fetch_newsdata")
    @patch("backend.app.services.news_service.fetch_google_news")
    def test_news_endpoint_upstream_failure_fallback_to_rss(self, mock_fetch_rss, mock_fetch_newsdata, mock_api_key):
        # Simulate NewsData.io throwing a runtime error
        mock_fetch_newsdata.side_effect = RuntimeError("NewsData.io rate limit exceeded")

        # Mock RSS fallback returning an article
        mock_fetch_rss.return_value = [
            {
                "title": "Fallback News Story via Google RSS",
                "description": "Fallback article description here.",
                "link": "https://news.google.com/rss/test",
                "country": ["in"],
                "source_id": "Google News",
                "pubDate": "2026-06-20 12:00:00"
            }
        ]

        payload = {
            "country": "in",
            "category": "General",
            "query": "",
            "max_articles": 5,
            "language": "en"
        }

        response = self.client.post("/api/news", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["source"], "google_news_rss")
        self.assertEqual(data["total_main"], 1)

    # --- Podcast Endpoint Tests ---
    @patch("backend.app.main.generate_dual_host_audio")
    def test_podcast_endpoint_success(self, mock_generate_audio):
        # Mock valid binary MP3 byte stream
        mock_bytes = b"ID3\x03\x00\x00\x00\x00\x00#MOCK_MP3_AUDIO_STREAM_DATA#"
        mock_generate_audio.return_value = io.BytesIO(mock_bytes)

        payload = {
            "category": "Technology & Software",
            "language": "en",
            "accent": "com",
            "main_articles": [
                {
                    "title": "AI models demonstrate new reasoning capabilities",
                    "summary": "Benchmarking results show significant advancements across logic tasks."
                }
            ],
            "mini_articles": [
                {
                    "title": "Tech stocks rally following hardware launch"
                }
            ]
        }

        response = self.client.post("/api/podcast", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/mpeg")
        self.assertIn("podcast_technology", response.headers.get("content-disposition", ""))
        self.assertEqual(response.content, mock_bytes)

    def test_podcast_endpoint_empty_articles_validation(self):
        payload = {
            "category": "General",
            "language": "en",
            "accent": "com",
            "main_articles": [],
            "mini_articles": []
        }
        response = self.client.post("/api/podcast", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("At least one article", response.json()["detail"])

    def test_podcast_endpoint_invalid_language(self):
        payload = {
            "category": "General",
            "language": "invalid_lang",
            "accent": "com",
            "main_articles": [{"title": "Sample Story"}]
        }
        response = self.client.post("/api/podcast", json=payload)
        self.assertEqual(response.status_code, 422)

    @patch("backend.app.main.generate_dual_host_audio")
    def test_podcast_endpoint_audio_generation_failure(self, mock_generate_audio):
        # Simulate TTS returning None (e.g. service unreachable)
        mock_generate_audio.return_value = None

        payload = {
            "category": "General",
            "language": "en",
            "accent": "com",
            "main_articles": [{"title": "Sample Story", "summary": "Sample Summary"}]
        }

        response = self.client.post("/api/podcast", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn("Failed to synthesize podcast audio", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
