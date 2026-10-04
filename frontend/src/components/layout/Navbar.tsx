import React from 'react';
import { ShieldIcon, TerminalIcon } from '../common/Icons';
import { getApiBaseUrl } from '../../services/api';

interface NavbarProps {
  onReset?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onReset }) => {
  const apiBase = getApiBaseUrl();

  return (
    <header className="console-navbar">
      <div className="container nav-container">
        {/* Brand identity */}
        <div
          className="nav-brand"
          onClick={onReset}
          role="button"
          tabIndex={0}
          title="Reset to Investigation Command Deck"
        >
          <div className="brand-cyber-shield">
            <ShieldIcon size={22} className="shield-icon" />
            <span className="shield-beacon" />
          </div>
          <div className="brand-naming">
            <div className="brand-logo-row">
              <span className="brand-title">VERITO</span>
              <span className="brand-version-tag">v1.0-EXP</span>
            </div>
            <span className="brand-subtext">Evidence Intelligence &amp; Claim Verification</span>
          </div>
        </div>

        {/* Telemetry metadata */}
        <div className="nav-telemetry">
          <div className="telemetry-pill hide-tablet">
            <span className="pill-beacon" />
            <span className="pill-label">ENGINE:</span>
            <span className="pill-val">TRACEABLE-GRAPH</span>
          </div>

          <div className="telemetry-pill">
            <TerminalIcon size={12} className="pill-icon" />
            <span className="pill-label">TARGET API:</span>
            <code className="pill-endpoint">{apiBase.replace(/^https?:\/\//, '')}</code>
          </div>
        </div>
      </div>
    </header>
  );
};
