import React from 'react';
import type { EvidenceItem } from '../../types/verification';
import { EvidenceCard } from './EvidenceCard';
import { CheckCircleIcon, XCircleIcon, GitBranchIcon } from '../common/Icons';

interface EvidenceSectionProps {
  supportingEvidence?: EvidenceItem[];
  contradictingEvidence?: EvidenceItem[];
}

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({
  supportingEvidence = [],
  contradictingEvidence = [],
}) => {
  const hasSupporting = supportingEvidence.length > 0;
  const hasContradicting = contradictingEvidence.length > 0;

  return (
    <section className="evidence-matrix-section" aria-labelledby="evidence-heading">
      {/* Matrix Header */}
      <div className="matrix-header">
        <div className="matrix-title-group">
          <GitBranchIcon size={16} className="matrix-header-icon" />
          <h3 id="evidence-heading" className="matrix-main-title">
            EVIDENCE COMPARISON &amp; STANCE MAPPING
          </h3>
        </div>
        <p className="matrix-description">
          Cross-referenced evidence collected from fact-checking registries, media archives, and authoritative databases.
        </p>
      </div>

      {/* 2-Column Comparison Layout */}
      <div className="matrix-grid">
        {/* Supporting Findings Column */}
        <div className="matrix-column column-supporting">
          <div className="column-top-bar bar-supporting">
            <div className="column-title-wrap">
              <CheckCircleIcon size={16} className="column-status-icon icon-supporting" />
              <h4 className="column-heading">CORROBORATING EVIDENCE</h4>
            </div>
            <span className="column-count-chip chip-supporting">
              {supportingEvidence.length} {supportingEvidence.length === 1 ? 'RECORD' : 'RECORDS'}
            </span>
          </div>

          <div className="column-records-list">
            {hasSupporting ? (
              supportingEvidence.map((item, idx) => (
                <EvidenceCard
                  key={`supp-${idx}`}
                  evidence={item}
                  type="supporting"
                  index={idx}
                />
              ))
            ) : (
              <div className="empty-record-state">
                <span className="empty-state-icon">&minus;</span>
                <p className="empty-state-title">No Corroborating Evidence Found</p>
                <p className="empty-state-desc">
                  None of the consulted fact-checking databases or news sources corroborated this claim.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Contradicting Findings Column */}
        <div className="matrix-column column-contradicting">
          <div className="column-top-bar bar-contradicting">
            <div className="column-title-wrap">
              <XCircleIcon size={16} className="column-status-icon icon-contradicting" />
              <h4 className="column-heading">CONTRADICTING EVIDENCE</h4>
            </div>
            <span className="column-count-chip chip-contradicting">
              {contradictingEvidence.length} {contradictingEvidence.length === 1 ? 'RECORD' : 'RECORDS'}
            </span>
          </div>

          <div className="column-records-list">
            {hasContradicting ? (
              contradictingEvidence.map((item, idx) => (
                <EvidenceCard
                  key={`contra-${idx}`}
                  evidence={item}
                  type="contradicting"
                  index={idx}
                />
              ))
            ) : (
              <div className="empty-record-state">
                <span className="empty-state-icon">&minus;</span>
                <p className="empty-state-title">No Contradicting Evidence Found</p>
                <p className="empty-state-desc">
                  None of the consulted fact-checking databases or news sources directly refuted this claim.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
