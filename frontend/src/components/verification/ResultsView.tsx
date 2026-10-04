import React, { useState } from 'react';
import type { VerifyResponse } from '../../types/verification';
import { ClaimSection } from './ClaimSection';
import { EvidenceSection } from './EvidenceSection';
import { AnalysisSection } from './AnalysisSection';
import { SourcesSection } from './SourcesSection';
import { VerificationPipeline } from './VerificationPipeline';
import { RefreshCwIcon, TerminalIcon, CheckCircleIcon, ArrowRightIcon } from '../common/Icons';

interface ResultsViewProps {
  result: VerifyResponse;
  originalUrl: string;
  onNewVerification: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  result,
  originalUrl,
  onNewVerification,
}) => {
  const [copySuccess, setCopySuccess] = useState(false);

  const supportingCount = result.supporting_evidence?.length || 0;
  const contradictingCount = result.contradicting_evidence?.length || 0;
  const sourceCount = result.sources?.length || 0;

  const handleCopySummary = async () => {
    try {
      const summaryText = [
        `VERITO INVESTIGATION REPORT`,
        `Target URL: ${originalUrl}`,
        `Claim: ${result.claim || 'N/A'}`,
        `Status: ${result.status || 'UNSPECIFIED'}`,
        `Supporting Evidence: ${supportingCount} record(s)`,
        `Contradicting Evidence: ${contradictingCount} record(s)`,
        `Consulted Sources: ${sourceCount} source(s)`,
        result.analysis ? `\nAnalysis:\n${result.analysis}` : '',
      ]
        .filter(Boolean)
        .join('\n');

      await navigator.clipboard.writeText(summaryText);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2500);
    } catch {
      // Ignore clipboard write errors
    }
  };

  return (
    <div className="investigation-workspace">
      {/* Top Workspace Dossier Bar */}
      <div className="workspace-control-bar">
        <div className="control-bar-left">
          <div className="dossier-status-pill">
            <span className="pill-dot-active" />
            <span className="pill-text">INVESTIGATION TRACE ASSEMBLED</span>
          </div>
          <span className="dossier-id-code">DOSSIER // EVIDENCE-GRAPH</span>
        </div>

        <div className="control-bar-right">
          <button
            type="button"
            className="action-btn btn-copy-report"
            onClick={handleCopySummary}
            title="Copy plain-text investigation summary"
          >
            {copySuccess ? (
              <>
                <CheckCircleIcon size={14} />
                <span>COPIED DOSSIER</span>
              </>
            ) : (
              <>
                <TerminalIcon size={14} />
                <span>COPY SUMMARY</span>
              </>
            )}
          </button>

          <button
            type="button"
            className="action-btn btn-new-investigation"
            onClick={onNewVerification}
            title="Clear and investigate a new article URL"
          >
            <RefreshCwIcon size={14} />
            <span>NEW INVESTIGATION</span>
          </button>
        </div>
      </div>

      {/* Compact Completed Pipeline Flow */}
      <div className="workspace-pipeline-header">
        <VerificationPipeline mode="completed" compact={true} />
      </div>

      {/* 1. Primary Central Object: Claim Under Investigation */}
      <ClaimSection
        claim={result.claim}
        status={result.status}
        sourceUrl={originalUrl}
        supportingCount={supportingCount}
        contradictingCount={contradictingCount}
        sourceCount={sourceCount}
      />

      {/* 2. Evidence Comparison & Bifurcation Matrix */}
      <EvidenceSection
        supportingEvidence={result.supporting_evidence}
        contradictingEvidence={result.contradicting_evidence}
      />

      {/* 3. AI Evidence Synthesis & Contextual Reasoning */}
      <AnalysisSection analysis={result.analysis} />

      {/* 4. Full Provenance & Source Trace Matrix */}
      <SourcesSection sources={result.sources} />

      {/* Bottom Dispatch Actions */}
      <div className="workspace-footer-bar">
        <button
          type="button"
          className="workspace-restart-btn"
          onClick={onNewVerification}
        >
          <RefreshCwIcon size={16} />
          <span>INVESTIGATE ANOTHER ARTICLE</span>
          <ArrowRightIcon size={14} />
        </button>
      </div>
    </div>
  );
};
