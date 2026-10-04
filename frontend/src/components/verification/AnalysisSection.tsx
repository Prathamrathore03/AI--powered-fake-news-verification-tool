import React from 'react';
import { ShieldIcon, TerminalIcon } from '../common/Icons';

interface AnalysisSectionProps {
  analysis?: string;
}

export const AnalysisSection: React.FC<AnalysisSectionProps> = ({ analysis }) => {
  if (!analysis) {
    return null;
  }

  // Parse multi-paragraph analysis
  const paragraphs = analysis
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  return (
    <section className="analysis-debrief-card" aria-labelledby="analysis-heading">
      {/* Debrief Header */}
      <div className="debrief-header">
        <div className="debrief-header-left">
          <ShieldIcon size={16} className="debrief-icon" />
          <h3 id="analysis-heading" className="debrief-title">
            AI EVIDENCE SYNTHESIS &amp; REASONING
          </h3>
        </div>
        <div className="debrief-header-right">
          <span className="debrief-tag">SYNTHESIS ENGINE // REASONING MODEL</span>
        </div>
      </div>

      {/* Main Analysis Body */}
      <div className="debrief-body">
        {paragraphs.length > 0 ? (
          paragraphs.map((para, idx) => (
            <p key={idx} className="debrief-paragraph">
              {para}
            </p>
          ))
        ) : (
          <p className="debrief-paragraph">{analysis}</p>
        )}
      </div>

      {/* Epistemological Integrity Notice */}
      <div className="debrief-transparency-box">
        <div className="transparency-icon-box">
          <TerminalIcon size={14} />
        </div>
        <div className="transparency-text-box">
          <span className="transparency-heading">METHODOLOGICAL TRANSPARENCY:</span>
          <p className="transparency-content">
            This analytical synthesis is derived exclusively from corroborating and contradicting evidence retrieved for the claim.
            VERITO presents observable facts and logical reasoning rather than arbitrary percentage scores or black-box truth values.
          </p>
        </div>
      </div>
    </section>
  );
};
