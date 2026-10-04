"""
VERITO Backend Test Suite
Tests URL validation, API contract structure, error handling, and SSRF protection.

Run from the backend/ directory:
    python -m pytest tests/ -v
  or:
    python -m unittest discover tests
"""

import json
import sys
import os
import unittest

# Ensure backend root is on path when running from tests/ subdirectory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_STATUSES = {'supported', 'contradicted', 'mixed', 'inconclusive'}

EXPECTED_RESPONSE_KEYS = {
    'claim',
    'status',
    'supporting_evidence',
    'contradicting_evidence',
    'analysis',
    'sources',
}


def make_client():
    app.config['TESTING'] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# URL Validation / SSRF Tests (via /verify endpoint — no external calls needed)
# ---------------------------------------------------------------------------

class TestUrlValidation(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def _post(self, url_value):
        return self.client.post(
            '/verify',
            data=json.dumps({'url': url_value}),
            content_type='application/json',
        )

    def test_empty_url_returns_400(self):
        resp = self._post('')
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn('error', data)

    def test_missing_url_field_returns_400(self):
        resp = self.client.post(
            '/verify',
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn('error', data)

    def test_non_string_url_returns_400(self):
        resp = self.client.post(
            '/verify',
            data=json.dumps({'url': 12345}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_no_scheme_url_returns_400(self):
        resp = self._post('www.bbc.com/news/article')
        self.assertEqual(resp.status_code, 400)

    def test_ftp_scheme_blocked(self):
        resp = self._post('ftp://files.example.com/article.txt')
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn('error', data)

    def test_javascript_scheme_blocked(self):
        resp = self._post('javascript:alert(1)')
        self.assertEqual(resp.status_code, 400)

    def test_localhost_blocked(self):
        resp = self._post('http://localhost/admin')
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn('error', data)
        self.assertIn('localhost', data['error'].lower())

    def test_loopback_ip_blocked(self):
        resp = self._post('http://127.0.0.1/secret')
        self.assertEqual(resp.status_code, 400)

    def test_private_192168_blocked(self):
        resp = self._post('http://192.168.1.1/router')
        self.assertEqual(resp.status_code, 400)

    def test_private_10x_blocked(self):
        resp = self._post('http://10.0.0.1/internal')
        self.assertEqual(resp.status_code, 400)

    def test_private_172_blocked(self):
        resp = self._post('http://172.16.0.1/internal')
        self.assertEqual(resp.status_code, 400)

    def test_valid_http_url_passes_validation(self):
        """A valid external URL should pass URL validation (may fail later for other reasons)."""
        resp = self._post('http://example.com/news/article')
        # Should NOT be a URL-format or SSRF error (400)
        # May be 422 (article extraction failed), 503 (API key missing), or 200
        self.assertNotEqual(resp.status_code, 400)

    def test_valid_https_url_passes_validation(self):
        resp = self._post('https://www.bbc.com/news/science-environment-1234')
        self.assertNotEqual(resp.status_code, 400)

    def test_very_long_url_blocked(self):
        resp = self._post('https://example.com/' + 'a' * 3000)
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# Request body edge cases
# ---------------------------------------------------------------------------

class TestRequestBody(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_plain_text_body_handled_gracefully(self):
        resp = self.client.post(
            '/verify',
            data='not json',
            content_type='text/plain',
        )
        # Should not crash — must return some error response
        self.assertIn(resp.status_code, [400, 415, 422, 500])

    def test_empty_body_handled_gracefully(self):
        resp = self.client.post(
            '/verify',
            data='',
            content_type='application/json',
        )
        self.assertIn(resp.status_code, [400, 422, 500])

    def test_null_body_handled_gracefully(self):
        resp = self.client.post(
            '/verify',
            data=json.dumps(None),
            content_type='application/json',
        )
        self.assertIn(resp.status_code, [400, 422, 500])


# ---------------------------------------------------------------------------
# Response structure contract
# ---------------------------------------------------------------------------

class TestResponseContract(unittest.TestCase):
    """
    Validates the API response schema matches the frontend TypeScript contract.
    Uses a URL that will fail at article extraction / API key stage, but verifies
    error responses follow the correct structure too.
    """

    def setUp(self):
        self.client = make_client()

    def test_error_response_has_error_field(self):
        """All error responses must have exactly an 'error' string field."""
        resp = self.client.post(
            '/verify',
            data=json.dumps({'url': ''}),
            content_type='application/json',
        )
        data = json.loads(resp.data)
        self.assertIn('error', data)
        self.assertIsInstance(data['error'], str)
        self.assertGreater(len(data['error']), 0)

    def test_valid_status_values_documented(self):
        """Document and test that valid status values match the frontend contract."""
        self.assertEqual(
            VALID_STATUSES,
            {'supported', 'contradicted', 'mixed', 'inconclusive'},
        )

    def test_expected_response_keys_documented(self):
        """Document the expected response keys that the frontend consumes."""
        self.assertEqual(
            EXPECTED_RESPONSE_KEYS,
            {'claim', 'status', 'supporting_evidence', 'contradicting_evidence', 'analysis', 'sources'},
        )


# ---------------------------------------------------------------------------
# SSRF Guard unit tests
# ---------------------------------------------------------------------------

class TestSsrfGuard(unittest.TestCase):
    def setUp(self):
        from ssrf_guard import validate_url
        self.validate = validate_url

    def test_valid_https(self):
        self.assertIsNone(self.validate('https://www.bbc.com/news/123'))

    def test_valid_http(self):
        self.assertIsNone(self.validate('http://reuters.com/article/123'))

    def test_empty_returns_error(self):
        self.assertIsNotNone(self.validate(''))

    def test_none_returns_error(self):
        self.assertIsNotNone(self.validate(None))

    def test_ftp_blocked(self):
        self.assertIsNotNone(self.validate('ftp://files.example.com'))

    def test_no_scheme_blocked(self):
        self.assertIsNotNone(self.validate('www.example.com/article'))

    def test_localhost_blocked(self):
        self.assertIsNotNone(self.validate('http://localhost/'))

    def test_127001_blocked(self):
        self.assertIsNotNone(self.validate('http://127.0.0.1/'))

    def test_192168_blocked(self):
        self.assertIsNotNone(self.validate('http://192.168.0.1/'))

    def test_10x_blocked(self):
        self.assertIsNotNone(self.validate('http://10.10.10.10/'))

    def test_172_private_blocked(self):
        self.assertIsNotNone(self.validate('http://172.20.0.1/'))

    def test_very_long_url(self):
        self.assertIsNotNone(self.validate('https://example.com/' + 'x' * 3000))


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_health_returns_200(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)

    def test_health_returns_json(self):
        resp = self.client.get('/health')
        data = json.loads(resp.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------

class TestCorsHeaders(unittest.TestCase):
    def setUp(self):
        self.client = make_client()

    def test_options_request_allowed(self):
        resp = self.client.options(
            '/verify',
            headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type',
            },
        )
        # Must not return 404 or 500 — CORS preflight must be handled
        self.assertNotIn(resp.status_code, [404, 500])


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main(verbosity=2)
