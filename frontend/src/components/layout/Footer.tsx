import React from 'react';
import { getApiBaseUrl } from '../../services/api';
import { ShieldIcon } from '../common/Icons';

export const Footer: React.FC = () => {
  const apiUrl = getApiBaseUrl();

  return (
    <footer className="console-footer">
      <div className="container footer-container">
        {/* Core Product Principle Notice */}
        <div className="footer-principle-block">
          <div className="footer-brand-row">
            <ShieldIcon size={16} className="footer-shield-icon" />
            <span className="footer-brand-title">VERITO EVIDENCE INTELLIGENCE PLATFORM</span>
          </div>
          <p className="footer-disclaimer-text">
            Operating principle: <strong>Claim &rarr; Evidence &rarr; Comparison &rarr; Explanation &rarr; Sources</strong>.
            VERITO decomposes claims into verifiable assertions and presents observable corroboration.
            It does not manufacture arbitrary percentage scores or claim absolute truth.
          </p>
        </div>

        {/* System Spec & Telemetry */}
        <div className="footer-spec-block">
          <div className="spec-item">
            <span className="spec-label">INTEGRATION SPEC:</span>
            <code className="spec-code">POST {apiUrl}/verify</code>
          </div>
          <div className="spec-item">
            <span className="spec-label">CONTRACT:</span>
            <span className="spec-val">JSON (Claim, Evidence, Analysis, Sources)</span>
          </div>
          <div className="spec-item">
            <span className="spec-label">RUNTIME:</span>
            <span className="spec-val">Vite 8 &bull; React 19 &bull; TypeScript</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
