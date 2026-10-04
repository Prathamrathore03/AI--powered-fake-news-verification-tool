import React, { useState } from 'react';
import type { VerificationError } from '../../types/verification';
import { AlertCircleIcon, RefreshCwIcon, TerminalIcon } from '../common/Icons';

interface ErrorStateProps {
  error: VerificationError;
  onRetry: () => void;
  onEditUrl?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry, onEditUrl }) => {
  const [showTechnical, setShowTechnical] = useState(false);

  return (
    <div className="investigation-diagnostic-panel" role="alert">
      {/* Header */}
      <div className="diagnostic-header">
        <div className="diagnostic-header-left">
          <div className="diagnostic-icon-frame">
            <AlertCircleIcon size={20} className="diagnostic-alert-icon" />
          </div>
          <div className="diagnostic-title-wrap">
            <span className="diagnostic-tag">SYSTEM DIAGNOSTIC &bull; PROBE EXCEPTION</span>
            <h3 className="diagnostic-headline">{error.title}</h3>
          </div>
        </div>
        <span className="diagnostic-status-chip">EXECUTION HALTED</span>
      </div>

      {/* Primary User Explanation */}
      <div className="diagnostic-body">
        <p className="diagnostic-message">{error.message}</p>
      </div>

      {/* Action Suggestion */}
      {error.actionSuggestion && (
        <div className="diagnostic-suggestion-box">
          <div className="suggestion-header">
            <TerminalIcon size={14} className="suggestion-icon" />
            <span className="suggestion-label">RECOMMENDED REMEDIATION:</span>
          </div>
          <p className="suggestion-text">{error.actionSuggestion}</p>
        </div>
      )}

      {/* Technical Diagnostics Accordion */}
      {error.technicalDetails && (
        <div className="diagnostic-technical-accordion">
          <button
            type="button"
            className="technical-toggle-btn"
            onClick={() => setShowTechnical(!showTechnical)}
          >
            <span className="toggle-symbol">{showTechnical ? '[-]' : '[+]'}</span>
            <span>{showTechnical ? 'HIDE RAW TRACE TELEMETRY' : 'VIEW RAW TRACE TELEMETRY'}</span>
          </button>

          {showTechnical && (
            <pre className="technical-trace-log">
              <code>{error.technicalDetails}</code>
            </pre>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="diagnostic-action-strip">
        <button type="button" className="diag-btn diag-btn-primary" onClick={onRetry}>
          <RefreshCwIcon size={14} />
          <span>RETRY DISPATCH</span>
        </button>

        {onEditUrl && (
          <button type="button" className="diag-btn diag-btn-secondary" onClick={onEditUrl}>
            <span>EDIT TARGET URL</span>
          </button>
        )}
      </div>
    </div>
  );
};
