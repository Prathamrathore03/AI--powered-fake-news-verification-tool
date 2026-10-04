import React from 'react';
import { VerificationPipeline } from './VerificationPipeline';
import { TerminalIcon, ShieldIcon, ActivityIcon, GlobeIcon } from '../common/Icons';

interface LoadingStateProps {
  url: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ url }) => {
  return (
    <div className="investigation-loading-console" role="status" aria-live="polite">
      {/* Console Header Bar */}
      <div className="console-status-bar">
        <div className="status-bar-left">
          <ActivityIcon size={16} className="telemetry-activity-icon" />
          <span className="telemetry-title">INVESTIGATION PIPELINE IN PROGRESS</span>
        </div>
        <div className="status-bar-right">
          <span className="telemetry-chip chip-scanning">
            <span className="scanning-dot" />
            PROCESSING DISPATCH
          </span>
        </div>
      </div>

      {/* Target Dossier Readout */}
      <div className="loading-target-dossier">
        <div className="dossier-row">
          <span className="dossier-label">PROBE TARGET:</span>
          <span className="dossier-value-url" title={url}>
            <GlobeIcon size={14} className="url-globe-icon" />
            {url}
          </span>
        </div>
        <div className="dossier-row hide-mobile">
          <span className="dossier-label">PIPELINE PROTOCOL:</span>
          <span className="dossier-value">INDETERMINATE TRACE (HONEST SAMPLING)</span>
        </div>
      </div>

      {/* Central 7-Stage Pipeline Visualizer */}
      <div className="loading-pipeline-wrapper">
        <VerificationPipeline mode="processing" />
      </div>

      {/* Real-time Telemetry Terminal */}
      <div className="terminal-telemetry-box">
        <div className="terminal-header">
          <TerminalIcon size={14} />
          <span>PROBE TELEMETRY LOG</span>
        </div>
        <div className="terminal-body">
          <div className="terminal-line line-active">
            <span className="line-prefix">&gt;</span>
            <span className="line-time">[STAGE 01-02]</span>
            <span className="line-text">Article content extraction and central factual claim isolation initiated...</span>
          </div>
          <div className="terminal-line line-pending">
            <span className="line-prefix">&gt;</span>
            <span className="line-time">[STAGE 03-05]</span>
            <span className="line-text">Cross-referencing independent fact-checking databases &amp; contrasting corroborating vs contradicting findings...</span>
          </div>
          <div className="terminal-line line-pending">
            <span className="line-prefix">&gt;</span>
            <span className="line-time">[STAGE 06-07]</span>
            <span className="line-text">Synthesizing transparent AI reasoning and preparing traceable source citations...</span>
          </div>
        </div>
      </div>

      {/* Transparent Integrity Notice */}
      <div className="loading-integrity-note">
        <ShieldIcon size={14} className="integrity-icon" />
        <span>
          <strong>Transparent Verification:</strong> VERITO does not show artificial countdown timers or fake percentages.
          Results will be rendered as soon as the verification engine returns the evidence graph.
        </span>
      </div>
    </div>
  );
};
