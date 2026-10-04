/**
 * API Service Layer for VERITO
 * Manages communication with the Flask backend verification endpoint.
 */

import type { VerifyRequest, VerifyResponse, VerificationError } from '../types/verification';

/**
 * Retrieves the base API URL from the environment configuration.
 * Defaults to http://localhost:5000 for local Flask backend development.
 */
export function getApiBaseUrl(): string {
  // Access Vite environment variable safely across browser and test runtimes
  let envUrl: string | undefined;
  try {
    if (typeof import.meta !== 'undefined' && 'env' in import.meta && import.meta.env) {
      envUrl = import.meta.env.VITE_API_BASE_URL;
    }
  } catch {
    envUrl = undefined;
  }

  if (typeof envUrl === 'string' && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  return 'http://localhost:5000';
}

/**
 * Custom error class for API failures in VERITO
 */
export class ApiError extends Error {
  public structuredError: VerificationError;

  constructor(structuredError: VerificationError) {
    super(structuredError.message);
    this.name = 'ApiError';
    this.structuredError = structuredError;
  }
}

/**
 * Sends an article URL to the backend for claim extraction, evidence retrieval,
 * and AI verification.
 *
 * @param url The full HTTP/HTTPS URL of the article to verify
 * @returns Promise resolving to the structured VerifyResponse
 * @throws ApiError with human-readable error messages and remediation tips
 */
export async function verifyArticle(url: string): Promise<VerifyResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/verify`;

  const payload: VerifyRequest = { url };

  let response: Response;

  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (err: unknown) {
    // Network failure, connection refused, or CORS blockage
    const rawMessage = err instanceof Error ? err.message : String(err);
    
    throw new ApiError({
      title: 'Cannot Connect to Verification Service',
      message:
        'Could not reach the VERITO backend service. The server may be offline, still starting up, or blocked by network settings.',
      technicalDetails: `Failed to fetch from ${endpoint}: ${rawMessage}`,
      actionSuggestion:
        'Ensure the Flask backend is running on ' +
        baseUrl +
        ' and has CORS enabled (e.g. flask-cors).',
    });
  }

  // Handle HTTP status codes
  let responseData: any;
  try {
    responseData = await response.json();
  } catch {
    throw new ApiError({
      title: 'Malformed Server Response',
      message:
        'The verification server returned a non-JSON or malformed response. Status code: ' +
        response.status,
      technicalDetails: `Failed to parse response body as JSON. HTTP ${response.status} ${response.statusText}`,
      actionSuggestion: 'Please verify the backend endpoint implementation and response format.',
    });
  }

  if (!response.ok) {
    // Backend returned an error object (e.g., { "error": "...", "message": "..." })
    const serverErrorMessage =
      responseData?.error ||
      responseData?.message ||
      `Server returned HTTP ${response.status} (${response.statusText})`;

    throw new ApiError({
      title: 'Verification Request Failed',
      message: String(serverErrorMessage),
      technicalDetails: `HTTP ${response.status} ${response.statusText} from ${endpoint}`,
      actionSuggestion:
        response.status === 404
          ? 'Check that the /verify POST route is registered on your Flask application.'
          : response.status === 400
          ? 'Check that the URL sent in the request body is valid and accessible by the backend.'
          : 'Check backend server logs for details on the error.',
    });
  }

  // Validate the minimal structure of the response
  if (typeof responseData !== 'object' || responseData === null) {
    throw new ApiError({
      title: 'Unexpected Response Format',
      message: 'The server returned an unexpected response structure.',
      technicalDetails: 'Expected a JSON object but received ' + typeof responseData,
      actionSuggestion: 'Ensure the Flask endpoint returns a JSON dictionary conforming to the contract.',
    });
  }

  // Check if response contains an explicit backend error flag
  if (responseData.error && !responseData.claim && !responseData.analysis) {
    throw new ApiError({
      title: 'Verification Error',
      message: String(responseData.error),
      actionSuggestion: 'The backend reported an error while processing the article.',
    });
  }

  return responseData as VerifyResponse;
}
