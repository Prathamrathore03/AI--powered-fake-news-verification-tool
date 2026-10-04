import React, { useState, useId } from 'react';
import { TerminalIcon, ArrowRightIcon, GlobeIcon, AlertCircleIcon } from '../common/Icons';
import { validateArticleUrl } from '../../utils/urlValidator';

interface UrlInputProps {
  initialUrl?: string;
  isLoading: boolean;
  onVerify: (url: string) => void;
}

export const UrlInput: React.FC<UrlInputProps> = ({
  initialUrl = '',
  isLoading,
  onVerify,
}) => {
  const [url, setUrl] = useState(initialUrl);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputId = useId();

  // Real-time domain breakdown extraction
  let parsedDomain: string | null = null;
  try {
    if (url.trim().startsWith('http://') || url.trim().startsWith('https://')) {
      const u = new URL(url.trim());
      if (u.hostname && u.hostname.includes('.')) {
        parsedDomain = u.hostname.replace(/^www\./, '');
      }
    }
  } catch {
    parsedDomain = null;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const validation = validateArticleUrl(url);
    if (!validation.isValid) {
      setValidationError(validation.error || 'Please provide a valid article URL.');
      return;
    }

    onVerify(validation.normalizedUrl || url.trim());
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        setValidationError(null);
      }
    } catch {
      // Graceful fallback if clipboard permission isn't granted
    }
  };

  const handleClear = () => {
    setUrl('');
    setValidationError(null);
  };

  return (
    <div className="command-deck-container">
      {/* Console Deck Header */}
      <div className="command-deck-header">
        <div className="deck-header-left">
          <TerminalIcon size={14} className="deck-terminal-icon" />
          <span className="deck-title">INVESTIGATION COMMAND CONSOLE</span>
        </div>
        <div className="deck-header-right">
          <span className="deck-protocol-badge">TARGET // HTTP_GET</span>
          <span className="deck-status-indicator">
            <span className="deck-dot" />
            STANDBY
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="command-deck-form" noValidate>
        <div className="command-input-frame">
          <label htmlFor={inputId} className="sr-only">
            Target Article URL for Verification
          </label>

          <div className="command-input-prefix">
            <GlobeIcon size={16} className="prefix-icon" />
            <span className="prefix-protocol">URL:</span>
          </div>

          <input
            id={inputId}
            type="url"
            className={`command-text-input ${validationError ? 'input-invalid' : ''}`}
            placeholder="Paste news or article URL to verify (e.g. https://www.reuters.com/world/...)"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (validationError) setValidationError(null);
            }}
            disabled={isLoading}
            autoComplete="off"
            spellCheck="false"
            required
          />

          <div className="command-input-actions">
            {url && !isLoading && (
              <button
                type="button"
                className="deck-action-btn deck-clear-btn"
                onClick={handleClear}
                title="Clear target URL"
                aria-label="Clear input"
              >
                &times;
              </button>
            )}

            {!url && !isLoading && (
              <button
                type="button"
                className="deck-action-btn deck-paste-btn"
                onClick={handlePaste}
                title="Paste URL from clipboard"
              >
                PASTE
              </button>
            )}

            <button
              type="submit"
              className="deck-dispatch-btn"
              disabled={isLoading || !url.trim()}
              title="Dispatch verification query to backend"
            >
              {isLoading ? (
                <span className="dispatch-loading">
                  <span className="cyber-spinner" />
                  <span>ANALYZING...</span>
                </span>
              ) : (
                <span className="dispatch-content">
                  <span>VERIFY CLAIM</span>
                  <ArrowRightIcon size={14} className="dispatch-arrow" />
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Live Domain Metadata or Validation Notice */}
        <div className="command-deck-footer">
          {validationError ? (
            <div className="deck-alert deck-alert-error" role="alert">
              <AlertCircleIcon size={14} />
              <span>{validationError}</span>
            </div>
          ) : parsedDomain ? (
            <div className="deck-meta-info">
              <span className="meta-tag">TARGET HOST:</span>
              <code className="meta-domain">{parsedDomain}</code>
              <span className="meta-divider">&bull;</span>
              <span className="meta-hint">PRESS [ENTER &crarr;] TO DISPATCH PROBE</span>
            </div>
          ) : (
            <div className="deck-meta-info deck-meta-subtle">
              <span className="meta-hint">
                Provide a complete article link. VERITO will isolate central claims, query fact-check registries, and contrast evidence.
              </span>
            </div>
          )}
        </div>
      </form>
    </div>
  );
};
