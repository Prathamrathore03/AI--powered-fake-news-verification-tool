import test from 'node:test';
import assert from 'node:assert/strict';
import { verifyArticle, ApiError } from './api.ts';

test('verifyArticle throws structured ApiError on connection failure / network error', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () => Promise.reject(new Error('connect ECONNREFUSED 127.0.0.1:5000'));

  try {
    await assert.rejects(
      async () => {
        await verifyArticle('https://www.example.com/news/123');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.structuredError.title, 'Cannot Connect to Verification Service');
        assert.match(err.structuredError.actionSuggestion || '', /flask-cors/i);
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('verifyArticle throws ApiError when server returns HTTP 500 with error JSON', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () =>
    Promise.resolve(
      new Response(JSON.stringify({ error: 'Article extraction failed: paywall encountered' }), {
        status: 500,
        statusText: 'Internal Server Error',
        headers: { 'Content-Type': 'application/json' },
      })
    );

  try {
    await assert.rejects(
      async () => {
        await verifyArticle('https://www.example.com/paywalled');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.structuredError.title, 'Verification Request Failed');
        assert.match(err.structuredError.message, /paywall encountered/i);
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('verifyArticle throws ApiError when server returns malformed HTML instead of JSON', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () =>
    Promise.resolve(
      new Response('<html><body>502 Bad Gateway</body></html>', {
        status: 502,
        statusText: 'Bad Gateway',
        headers: { 'Content-Type': 'text/html' },
      })
    );

  try {
    await assert.rejects(
      async () => {
        await verifyArticle('https://www.example.com/news/article');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.structuredError.title, 'Malformed Server Response');
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('verifyArticle parses valid verification response successfully', async () => {
  const mockBackendPayload = {
    claim: 'Solar storms will permanently shut down all telecommunications next week.',
    status: 'contradicted',
    supporting_evidence: [],
    contradicting_evidence: [
      {
        title: 'NASA clarifies solar flare advisory',
        url: 'https://nasa.gov/article/1',
        source: 'NASA',
        snippet: 'Routine geomagnetic activity poses no threat to global communication grids.',
      },
    ],
    analysis: 'Space weather agencies confirm that geomagnetic disturbances are within normal ranges.',
    sources: [
      {
        title: 'NASA Space Weather Prediction',
        url: 'https://nasa.gov/article/1',
        source: 'NASA',
      },
    ],
  };

  const originalFetch = globalThis.fetch;
  globalThis.fetch = () =>
    Promise.resolve(
      new Response(JSON.stringify(mockBackendPayload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

  try {
    const result = await verifyArticle('https://www.example.com/news/solar-storms');
    assert.equal(result.claim, mockBackendPayload.claim);
    assert.equal(result.status, 'contradicted');
    assert.equal(result.contradicting_evidence?.length, 1);
    assert.equal(result.contradicting_evidence?.[0].source, 'NASA');
  } finally {
    globalThis.fetch = originalFetch;
  }
});
