"""
Pipeline Mocked Integration Test Suite for VERITO

Tests the complete verification pipeline with mocked external network services
to verify robustness without consuming external quotas or requiring active network.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, _CACHE


class TestPipelineMocked(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        _CACHE.clear()

    @patch('app.extract_article')
    @patch('app.extract_claim')
    @patch('app.search_fact_checks')
    @patch('app.search_evidence')
    @patch('app.classify_evidence')
    @patch('app.synthesize_analysis')
    def test_complete_successful_verification_flow(
        self,
        mock_synthesize,
        mock_classify,
        mock_search_evidence,
        mock_search_fact,
        mock_extract_claim,
        mock_extract_article,
    ):
        """Test complete successful verification response conforms to schema."""
        mock_extract_article.return_value = {
            "title": "Scientists Discover New Water Source on Moon",
            "text": "Researchers using satellite data have confirmed subsurface ice deposits.",
            "author": "Science Reporter",
            "date": "2026-10-01",
        }
        mock_extract_claim.return_value = "Scientists confirmed water ice deposits on the Moon."
        mock_search_fact.return_value = []
        mock_search_evidence.return_value = [
            {
                "title": "NASA data confirms lunar ice deposits",
                "source": "nature.com",
                "url": "https://nature.com/articles/lunar-ice",
                "snippet": "New spectral analysis proves significant ice in shaded lunar craters.",
            },
            {
                "title": "Lunar water discovery verified by international team",
                "source": "bbc.com",
                "url": "https://bbc.com/news/science-lunar",
                "snippet": "Independent instruments confirm presence of ice deposits.",
            },
        ]
        mock_classify.return_value = (
            [
                {
                    "title": "NASA data confirms lunar ice deposits",
                    "source": "nature.com",
                    "url": "https://nature.com/articles/lunar-ice",
                    "snippet": "New spectral analysis proves significant ice in shaded lunar craters.",
                },
                {
                    "title": "Lunar water discovery verified by international team",
                    "source": "bbc.com",
                    "url": "https://bbc.com/news/science-lunar",
                    "snippet": "Independent instruments confirm presence of ice deposits.",
                },
            ],
            [],
        )
        mock_synthesize.return_value = {
            "status": "supported",
            "analysis": "The claim is well-corroborated by astronomical spectral analysis from multiple research organizations.",
        }

        resp = self.client.post(
            '/verify',
            data=json.dumps({'url': 'https://example.com/moon-water-discovery'}),
            content_type='application/json',
        )

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        # Check all required response keys are present
        self.assertIn('claim', data)
        self.assertIn('status', data)
        self.assertIn('supporting_evidence', data)
        self.assertIn('contradicting_evidence', data)
        self.assertIn('analysis', data)
        self.assertIn('sources', data)

        self.assertEqual(data['status'], 'supported')
        self.assertEqual(len(data['supporting_evidence']), 2)
        self.assertEqual(len(data['contradicting_evidence']), 0)
        self.assertEqual(len(data['sources']), 2)
        self.assertTrue(all('url' in s for s in data['sources']))

    @patch('app.extract_article')
    def test_article_extraction_failure_returns_422(self, mock_extract):
        """When article content cannot be extracted, return clean 422 error."""
        mock_extract.side_effect = ValueError(
            "Could not extract meaningful article content from this URL. Page may be paywalled."
        )

        resp = self.client.post(
            '/verify',
            data=json.dumps({'url': 'https://example.com/paywalled-article'}),
            content_type='application/json',
        )

        self.assertEqual(resp.status_code, 422)
        data = json.loads(resp.data)
        self.assertIn('error', data)
        self.assertIn('paywalled', data['error'])

    @patch('app.extract_article')
    @patch('app.extract_claim')
    def test_missing_api_key_returns_503(self, mock_extract_claim, mock_extract_article):
        """When GEMINI_API_KEY is missing, return 503 Service Unavailable."""
        mock_extract_article.return_value = {"title": "Title", "text": "Article text content here."}
        mock_extract_claim.side_effect = EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to backend/.env."
        )

        resp = self.client.post(
            '/verify',
            data=json.dumps({'url': 'https://example.com/some-news-story'}),
            content_type='application/json',
        )

        self.assertEqual(resp.status_code, 503)
        data = json.loads(resp.data)
        self.assertIn('error', data)
        self.assertIn('GEMINI_API_KEY', data['error'])

    @patch('app.extract_article')
    @patch('app.extract_claim')
    @patch('app.search_fact_checks')
    @patch('app.search_evidence')
    @patch('app.classify_evidence')
    @patch('app.synthesize_analysis')
    def test_caching_returns_identical_result_without_recalculating(
        self,
        mock_synthesize,
        mock_classify,
        mock_search_evidence,
        mock_search_fact,
        mock_extract_claim,
        mock_extract_article,
    ):
        """Calling /verify with identical URL within TTL returns cached result."""
        mock_extract_article.return_value = {"title": "Cached Title", "text": "Text content."}
        mock_extract_claim.return_value = "A verifiable claim."
        mock_search_fact.return_value = []
        mock_search_evidence.return_value = []
        mock_classify.return_value = ([], [])
        mock_synthesize.return_value = {"status": "inconclusive", "analysis": "Inconclusive analysis."}

        test_url = 'https://example.com/cached-article-test'

        # First call: executes pipeline
        resp1 = self.client.post(
            '/verify',
            data=json.dumps({'url': test_url}),
            content_type='application/json',
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(mock_extract_article.call_count, 1)

        # Second call: served from cache!
        resp2 = self.client.post(
            '/verify',
            data=json.dumps({'url': test_url}),
            content_type='application/json',
        )
        self.assertEqual(resp2.status_code, 200)
        # mock_extract_article should NOT have been called a second time
        self.assertEqual(mock_extract_article.call_count, 1)

        data1 = json.loads(resp1.data)
        data2 = json.loads(resp2.data)
        self.assertEqual(data1, data2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
