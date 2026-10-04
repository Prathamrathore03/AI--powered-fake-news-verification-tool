import test from 'node:test';
import assert from 'node:assert/strict';
import { validateArticleUrl } from './urlValidator.ts';

test('validateArticleUrl rejects empty string', () => {
  const result = validateArticleUrl('');
  assert.equal(result.isValid, false);
  assert.match(result.error || '', /enter a news or article URL/i);
});

test('validateArticleUrl rejects whitespace string', () => {
  const result = validateArticleUrl('   ');
  assert.equal(result.isValid, false);
  assert.match(result.error || '', /enter a news or article URL/i);
});

test('validateArticleUrl detects missing protocol and provides guidance', () => {
  const result = validateArticleUrl('bbc.com/news/world-12345');
  assert.equal(result.isValid, false);
  assert.match(result.error || '', /https:\/\/bbc.com/i);
});

test('validateArticleUrl rejects unsupported protocols like ftp or javascript', () => {
  const result = validateArticleUrl('ftp://example.com/file.txt');
  assert.equal(result.isValid, false);
});

test('validateArticleUrl rejects invalid domains without TLD', () => {
  const result = validateArticleUrl('http://localhost');
  assert.equal(result.isValid, false);
  assert.match(result.error || '', /complete domain name/i);
});

test('validateArticleUrl accepts valid HTTPS URL', () => {
  const result = validateArticleUrl('https://www.reuters.com/world/europe/article-id-12345');
  assert.equal(result.isValid, true);
  assert.equal(result.error, undefined);
  assert.equal(result.normalizedUrl, 'https://www.reuters.com/world/europe/article-id-12345');
});

test('validateArticleUrl accepts valid HTTP URL and trims whitespace', () => {
  const result = validateArticleUrl('   http://apnews.com/article/press-release   ');
  assert.equal(result.isValid, true);
  assert.equal(result.normalizedUrl, 'http://apnews.com/article/press-release');
});
