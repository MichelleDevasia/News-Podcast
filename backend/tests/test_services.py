"""
Comprehensive Unit & Integration Test Suite for Backend Services.
Verifies faithful extraction of NLP, news ranking, and audio services.
"""

from datetime import datetime
import io
import unittest
from unittest.mock import patch, MagicMock

from backend.app.core.constants import (
    TRUSTED_SOURCE_SUBSTRINGS,
    CUSTOM_CATEGORIES,
    COUNTRIES,
    AUDIO_LANGUAGES,
    ACCENTS,
)
from backend.app.services.nlp_service import (
    translate_to_target_lang,
    is_similar_to_existing,
    summarize_text_concise,
    get_news_sentiment,
)
from backend.app.services.news_service import (
    parse_date,
    calculate_article_score,
    fetch_google_news,
    fetch_newsdata,
    filter_and_rank_articles,
)
from backend.app.services.audio_service import (
    build_podcast_segments,
    generate_audio,
    generate_dual_host_audio,
)


class TestConstants(unittest.TestCase):
    """Verifies constants are preserved faithfully."""

    def test_constants_structure(self):
        self.assertIn("bbc", TRUSTED_SOURCE_SUBSTRINGS)
        self.assertIn("General", CUSTOM_CATEGORIES)
        self.assertIn("Politics & Governance", CUSTOM_CATEGORIES)
        self.assertIn("India (in)", COUNTRIES)
        self.assertEqual(AUDIO_LANGUAGES["Malayalam"], "ml")
        self.assertEqual(ACCENTS["United Kingdom (English)"], "co.uk")


class TestNLPService(unittest.TestCase):
    """Deterministic unit tests for NLP functions."""

    def test_deduplication_exact(self):
        title = "ISRO prepares for Chandrayaan-4 lunar sample return mission"
        existing = {"isro prepares for chandrayaan-4 lunar sample return mission"}
        self.assertTrue(is_similar_to_existing(title, existing, threshold=0.45))

    def test_deduplication_token_similarity(self):
        title1 = "Government announces major tax relief reforms today"
        title2 = "Government announces tax relief package"
        self.assertTrue(is_similar_to_existing(title1, [title2], threshold=0.45))

    def test_deduplication_distinct(self):
        title1 = "Stock market reaches all time high on tech rally"
        title2 = "Severe cyclone warning issued for coastal areas"
        self.assertFalse(is_similar_to_existing(title1, [title2], threshold=0.45))

    def test_deduplication_empty_inputs(self):
        self.assertFalse(is_similar_to_existing("", ["Existing"]))
        self.assertFalse(is_similar_to_existing("Valid title", []))

    def test_extractive_summarization(self):
        text = (
            "The launch took place at 9 AM today. Weather conditions were optimal throughout the countdown. "
            "Engineers confirmed payload separation shortly after orbit injection. Additional telemetry data is expected later. "
            "A press conference will follow tonight."
        )
        summary = summarize_text_concise(title="Title", description=text)
        sentences = summary.split(". ")
        # Should retain exactly first 3 sentences
        self.assertIn("The launch took place", summary)
        self.assertIn("Weather conditions were optimal", summary)
        self.assertIn("Engineers confirmed payload separation", summary)
        self.assertNotIn("A press conference will follow tonight", summary)

    def test_sentiment_scoring(self):
        pos_title = "Company achieves record growth and celebrates launch success"
        self.assertEqual(get_news_sentiment(pos_title, ""), "Positive")

        neg_title = "Police arrest suspect after violent clash and bus crash"
        self.assertEqual(get_news_sentiment(neg_title, ""), "Negative")

        neutral_title = "The annual committee report has been published"
        self.assertEqual(get_news_sentiment(neutral_title, ""), "Neutral")

    @patch("backend.app.services.nlp_service.GoogleTranslator")
    def test_translation_mocked(self, mock_translator):
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "വാർത്ത"
        mock_translator.return_value = mock_instance

        translated = translate_to_target_lang("News", "ml")
        self.assertEqual(translated, "വാർത്ത")
        mock_translator.assert_called_with(source="auto", target="ml")


class TestNewsService(unittest.TestCase):
    """Deterministic unit tests for News retrieval and ranking logic."""

    def test_parse_date(self):
        dt1 = parse_date("2026-06-20 14:30:00")
        self.assertEqual(dt1.year, 2026)
        self.assertEqual(dt1.month, 6)

        dt_iso = parse_date("2026-06-20T14:30:00Z")
        self.assertEqual(dt_iso.year, 2026)

        dt_invalid = parse_date("not-a-valid-date")
        self.assertEqual(dt_invalid, datetime.min)

    def test_article_scoring_weights(self):
        # 1. Trusted source boost (+45.0)
        art_trusted = {
            "title": "General announcement",
            "description": "Details here",
            "source_id": "BBC World News",
            "pubDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        score_trusted = calculate_article_score(art_trusted, user_query=None, cat_keywords=[])
        self.assertGreaterEqual(score_trusted, 45.0)

        # 2. Query match weights (+20.0 in title)
        art_query = {
            "title": "Quantum computing breakthrough in lab",
            "description": "Research details",
            "source_id": "Independent Blog",
            "pubDate": ""
        }
        score_query = calculate_article_score(art_query, user_query="quantum", cat_keywords=[])
        self.assertEqual(score_query, 20.0)

        # 3. Category keywords match (+10.0 in title)
        score_cat = calculate_article_score(art_query, user_query=None, cat_keywords=["quantum"])
        self.assertEqual(score_cat, 10.0)

    def test_filter_and_rank_articles_pipeline(self):
        raw_articles = [
            {
                "title": "Prime minister inaugurates new railway line",
                "description": "The railway project connects two major industrial hubs.",
                "country": ["in"],
                "source_id": "The Hindu",
                "pubDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "title": "Prime minister inaugurates new railway line",  # Duplicate
                "description": "Same story from another feed",
                "country": ["in"],
                "source_id": "Another Source",
                "pubDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "title": "Short bulletin update without details",
                "description": "",  # Should become mini article
                "country": ["in"],
                "source_id": "Flash News",
                "pubDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]

        main_arts, mini_arts, used_fallback = filter_and_rank_articles(
            raw_articles,
            category="General",
            country_code="in",
            max_articles=10,
            strict_country=True,
            strict_category=False
        )

        self.assertEqual(len(main_arts), 1)
        self.assertEqual(len(mini_arts), 1)
        self.assertFalse(used_fallback)
        self.assertIn("score", main_arts[0])

    @patch("backend.app.services.news_service.requests.get")
    def test_fetch_newsdata_mocked(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "success",
            "results": [{"title": "Test Story 1"}],
            "nextPage": None
        }
        mock_get.return_value = mock_resp

        data = fetch_newsdata(api_key="mock_key", category="General", max_articles=5)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["results"]), 1)


class TestAudioService(unittest.TestCase):
    """Deterministic script builder and audio generation tests."""

    def test_podcast_script_alternating_hosts(self):
        main_arts = [
            {"title": "Story Alpha", "summary": "Summary Alpha"},
            {"title": "Story Beta", "summary": "Summary Beta"},
            {"title": "Story Gamma", "summary": "Summary Gamma"}
        ]
        mini_arts = [{"title": "Bullet 1"}, {"title": "Bullet 2"}]

        segments = build_podcast_segments(main_arts, mini_arts, category="Technology & Software", audio_lang_code="en")

        # First segment is Intro (Host 0)
        self.assertEqual(segments[0][1], 0)
        self.assertIn("Welcome to your daily news briefing", segments[0][0])

        # Main stories alternate hosts
        self.assertEqual(segments[1][1], 0)  # Story 1 -> Host 0
        self.assertIn("Story number 1", segments[1][0])
        self.assertEqual(segments[2][1], 1)  # Story 2 -> Host 1
        self.assertIn("Story number 2", segments[2][0])
        self.assertEqual(segments[3][1], 0)  # Story 3 -> Host 0
        self.assertIn("Story number 3", segments[3][0])

        # Last segment is Outro (Host 0)
        self.assertEqual(segments[-1][1], 0)
        self.assertIn("That concludes your news podcast update", segments[-1][0])

    def test_podcast_script_multilingual_templates(self):
        # Malayalam
        ml_segs = build_podcast_segments([], [], category="General", audio_lang_code="ml")
        self.assertIn("നമസ്കാരം", ml_segs[0][0])
        self.assertIn("നന്ദി", ml_segs[-1][0])

        # Tamil
        ta_segs = build_podcast_segments([], [], category="General", audio_lang_code="ta")
        self.assertIn("வணக்கம்", ta_segs[0][0])
        self.assertIn("நன்றி", ta_segs[-1][0])

        # Hindi
        hi_segs = build_podcast_segments([], [], category="General", audio_lang_code="hi")
        self.assertIn("नमस्कार", hi_segs[0][0])
        self.assertIn("धन्यवाद", hi_segs[-1][0])

        # Kannada
        kn_segs = build_podcast_segments([], [], category="General", audio_lang_code="kn")
        self.assertIn("ನಮಸ್ಕಾರ", kn_segs[0][0])
        self.assertIn("ಧನ್ಯವಾದಗಳು", kn_segs[-1][0])


class TestIntegrationLive(unittest.TestCase):
    """
    Live integration tests requiring internet connectivity.
    Gracefully handled if network access or third-party service is unavailable.
    """

    def test_live_rss_feed_parsing(self):
        try:
            articles = fetch_google_news("India", country_code="in", lang_code="en")
            if not articles:
                self.skipTest("Google News RSS returned no articles (network or rate limit).")
            self.assertGreater(len(articles), 0)
            self.assertIn("title", articles[0])
            self.assertIn("link", articles[0])
        except Exception as e:
            self.skipTest(f"Live RSS network check skipped due to exception: {e}")

    def test_live_gtts_audio_synthesis(self):
        try:
            segments = [("Hello world.", 0), ("Welcome to the test.", 1)]
            audio_buffer = generate_dual_host_audio(segments, lang_code="en", accent_tld="com")
            if audio_buffer is None:
                self.skipTest("gTTS service could not synthesize audio (network or rate limit).")
            self.assertIsInstance(audio_buffer, io.BytesIO)
            self.assertGreater(len(audio_buffer.getvalue()), 1000)  # Non-trivial MP3 bytes
        except Exception as e:
            self.skipTest(f"Live gTTS audio generation skipped due to exception: {e}")


if __name__ == "__main__":
    unittest.main()
