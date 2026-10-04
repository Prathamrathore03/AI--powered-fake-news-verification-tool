import React from 'react';
import { StatusBadge } from './StatusBadge';
import { ExternalLinkIcon, FileTextIcon, GlobeIcon } from '../common/Icons';

interface ClaimSectionProps {
  claim?: string;
  status?: string;
  sourceUrl?: string;
  supportingCount?: number;
  contradictingCount?: number;
  sourceCount?: number;
}

export const ClaimSection: React.FC<ClaimSectionProps> = ({
  claim,
  status,
  sourceUrl,
  supportingCount = 0,
  contradictingCount = 0,
  sourceCount = 0,
}) => {
  return (
    <section className="claim-investigation-card" aria-labelledby="claim-heading">
      {/* Dossier Header */}
      <div className="claim-dossier-header">
        <div className="dossier-header-left">
          <FileTextIcon size={16} className="dossier-icon" />
          <span className="dossier-tag">SUBJECT CLAIM UNDER INVESTIGATION</span>
        </div>
        <div className="dossier-header-right">
          <span className="dossier-id-chip">DOSSIER // PRIMARY_ASSERTION</span>
        </div>
      </div>

      {/* Main Claim Quotation Box */}
      <div className="claim-body-container">
        <div className="claim-quote-bracket" aria-hidden="true">&ldquo;</div>

        <div className="claim-main-content">
          <h2 id="claim-heading" className="claim-assertion-text">
            {claim || 'No explicit claim text extracted from target source.'}
          </h2>

          {/* Analyzed Article Reference */}
          {sourceUrl && (
            <div className="claim-source-provenance">
              <span className="provenance-label">SOURCE ARTICLE:</span>
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="provenance-link"
                title="View original article in new tab"
              >
                <GlobeIcon size={13} />
                <span className="provenance-url-text">{sourceUrl}</span>
                <ExternalLinkIcon size={12} className="provenance-ext-icon" />
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Evaluation Footer & Status Telemetry */}
      <div className="claim-dossier-footer">
        <div className="footer-status-group">
          <span className="footer-status-label">FINDING STATUS:</span>
          {status ? (
            <StatusBadge status={status} size="lg" />
          ) : (
            <span className="status-unspecified">AWAITING CLASSIFICATION</span>
          )}
        </div>

        <div className="footer-telemetry-chips">
          <div className="telemetry-chip chip-supporting">
            <span className="chip-count">{supportingCount}</span>
            <span className="chip-label">CORROBORATING</span>
          </div>
          <div className="telemetry-chip chip-contradicting">
            <span className="chip-count">{contradictingCount}</span>
            <span className="chip-label">CONTRADICTING</span>
          </div>
          <div className="telemetry-chip chip-sources">
            <span className="chip-count">{sourceCount}</span>
            <span className="chip-label">CONSULTED SOURCES</span>
          </div>
        </div>
      </div>

      {/* Schematic Fork Node to Branching Evidence */}
      <div className="schematic-fork-node" aria-hidden="true">
        <div className="fork-stem" />
        <div className="fork-junction">
          <span className="junction-dot" />
          <span className="junction-label">EVIDENCE BIFURCATION</span>
        </div>
        <div className="fork-arms">
          <div className="fork-arm fork-arm-left" />
          <div className="fork-arm fork-arm-right" />
        </div>
      </div>
    </section>
  );
};
