/**
 * URL validation helper for VERITO
 */

export interface UrlValidationResult {
  isValid: boolean;
  error?: string;
  normalizedUrl?: string;
}

/**
 * Validates a user-provided article URL.
 * Ensures the URL is non-empty, uses HTTP or HTTPS protocol, and has a valid hostname.
 */
export function validateArticleUrl(rawUrl: string): UrlValidationResult {
  const trimmed = rawUrl.trim();

  if (!trimmed) {
    return {
      isValid: false,
      error: 'Please enter a news or article URL to verify.',
    };
  }

  // Check if user forgot protocol, or used something invalid
  let urlToTest = trimmed;
  if (!/^https?:\/\//i.test(trimmed)) {
    // If it looks like a domain (e.g. reuters.com/news/123), suggest http/https
    if (/^[\w.-]+\.[a-z]{2,}/i.test(trimmed)) {
      return {
        isValid: false,
        error: 'Please include the URL protocol (e.g. https://' + trimmed + ').',
      };
    }
    return {
      isValid: false,
      error: 'Invalid URL format. Please provide a full web address starting with http:// or https://',
    };
  }

  try {
    const parsed = new URL(urlToTest);

    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return {
        isValid: false,
        error: 'Only standard web URLs (http:// or https://) are supported.',
      };
    }

    if (!parsed.hostname || !parsed.hostname.includes('.')) {
      return {
        isValid: false,
        error: 'Please provide a valid article URL with a complete domain name.',
      };
    }

    return {
      isValid: true,
      normalizedUrl: parsed.toString(),
    };
  } catch {
    return {
      isValid: false,
      error: 'The provided text is not a valid URL. Please check for typos and try again.',
    };
  }
}
