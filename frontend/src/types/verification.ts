/**
 * Type definitions for VERITO - AI-powered Fake News Verification Tool
 */

/**
 * Single piece of evidence returned by the backend
 */
export interface EvidenceItem {
  title?: string;
  url?: string;
  source?: string;
  snippet?: string;
}

/**
 * Source citation returned by the backend
 */
export interface SourceItem {
  title?: string;
  url: string;
  source?: string;
  description?: string;
}

/**
 * Expected response contract from POST /verify
 */
export interface VerifyResponse {
  claim?: string;
  supporting_evidence?: EvidenceItem[];
  contradicting_evidence?: EvidenceItem[];
  analysis?: string;
  sources?: (SourceItem | string)[];
  status?: string;
  error?: string;
  message?: string;
}

/**
 * Request payload sent to POST /verify
 */
export interface VerifyRequest {
  url: string;
}

/**
 * High-level state of the verification UI
 */
export type VerificationViewStatus = 'idle' | 'loading' | 'results' | 'error';

/**
 * Structured user-facing error details
 */
export interface VerificationError {
  title: string;
  message: string;
  technicalDetails?: string;
  actionSuggestion?: string;
}
