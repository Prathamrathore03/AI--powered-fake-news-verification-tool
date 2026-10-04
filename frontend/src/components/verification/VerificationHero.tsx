import React from 'react';
import { TerminalIcon } from '../common/Icons';

export const VerificationHero: React.FC = () => {
  return (
    <section className="investigation-hero">
      {/* Telemetry Header Badge */}
      <div className="telemetry-bar">
        <div className="telemetry-item">
          <span className="telemetry-pulse" />
          <span className="telemetry-label">SYSTEM:</span>
          <span className="telemetry-value">ONLINE // ACTIVE-PROBE</span>
        </div>
        <div className="telemetry-divider">/</div>
        <div className="telemetry-item">
          <span className="telemetry-label">ARCHITECTURE:</span>
          <span className="telemetry-value">EVIDENCE-FIRST / TRACEABLE</span>
        </div>
        <div className="telemetry-divider">/</div>
        <div className="telemetry-item hide-mobile">
          <span className="telemetry-label">EVALUATION:</span>
          <span className="telemetry-value">ZERO BLACK-BOX SCORES</span>
        </div>
      </div>

      {/* Main Title & Tagline */}
      <div className="hero-brand-block">
        <div className="hero-dossier-tag">
          <TerminalIcon size={14} className="hero-terminal-icon" />
          <span>INVESTIGATION CONSOLE &bull; FORENSIC TRACE ENGINE</span>
        </div>

        <h1 className="hero-headline">
          Investigate news claims using{' '}
          <span className="headline-gradient">traceable evidence</span> &amp; corroborated sources.
        </h1>

        <p className="hero-subtext">
          VERITO operates as an AI evidence research assistant. It decomposes articles into verifiable claims,
          cross-references independent fact-checking databases, and contrasts supporting versus contradicting evidence
          rather than manufacturing opaque confidence percentages.
        </p>
      </div>

      {/* Forensic Axiom Strip */}
      <div className="forensic-axiom-strip">
        <div className="axiom-node">
          <span className="axiom-label">01 / ISOLATE</span>
          <span className="axiom-title">Claim</span>
        </div>
        <span className="axiom-connector">&rarr;</span>
        <div className="axiom-node">
          <span className="axiom-label">02 / RETRIEVE</span>
          <span className="axiom-title">Evidence</span>
        </div>
        <span className="axiom-connector">&rarr;</span>
        <div className="axiom-node">
          <span className="axiom-label">03 / CONTRAST</span>
          <span className="axiom-title">Comparison</span>
        </div>
        <span className="axiom-connector">&rarr;</span>
        <div className="axiom-node">
          <span className="axiom-label">04 / SYNTHESIZE</span>
          <span className="axiom-title">Explanation</span>
        </div>
        <span className="axiom-connector">&rarr;</span>
        <div className="axiom-node">
          <span className="axiom-label">05 / VERIFY</span>
          <span className="axiom-title">Sources</span>
        </div>
      </div>
    </section>
  );
};
