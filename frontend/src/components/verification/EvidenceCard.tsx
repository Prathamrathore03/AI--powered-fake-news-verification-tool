import React from 'react';
import type { EvidenceItem } from '../../types/verification';
import { ExternalLinkIcon, CheckCircleIcon, XCircleIcon, GlobeIcon } from '../common/Icons';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  type: 'supporting' | 'contradicting';
  index?: number;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  type,
  index = 0,
}) => {
  const isSupporting = type === 'supporting';
  const Icon = isSupporting ? CheckCircleIcon : XCircleIcon;

  // Formatted record ID (e.g. EV-SUP-01, EV-CON-02)
  const prefix = isSupporting ? 'EV-SUP' : 'EV-CON';
  const recordId = `${prefix}-${String(index + 1).padStart(2, '0')}`;

  // Extract hostname if possible
  let hostname = '';
  if (evidence.url) {
    try {
      hostname = new URL(evidence.url).hostname.replace(/^www\./, '');
    } catch {
      hostname = '';
    }
  }

  return (
    <article className={`evidence-dossier-card card-stance-${type}`}>
      {/* Dossier Record Header */}
      <div className="dossier-record-header">
        <div className="record-identity">
          <span className="record-id-badge">{recordId}</span>
          <div className="record-source-tag">
            <GlobeIcon size={12} className="source-globe-icon" />
            <span className="source-publisher">{evidence.source || hostname || 'Independent Archive'}</span>
          </div>
        </div>

        <div className="record-stance-indicator">
          <Icon size={13} className="stance-icon" />
          <span className="stance-label">
            {isSupporting ? 'CORROBORATES' : 'CONTRADICTS'}
          </span>
        </div>
      </div>

      {/* Article / Finding Title */}
      {evidence.title && (
        <h4 className="dossier-headline">{evidence.title}</h4>
      )}

      {/* Verbatim Excerpt / Snippet Box */}
      <div className="dossier-excerpt-container">
        <div className="excerpt-label">CITED EXCERPT:</div>
        {evidence.snippet ? (
          <blockquote className="dossier-quote-text">
            &ldquo;{evidence.snippet}&rdquo;
          </blockquote>
        ) : (
          <p className="dossier-no-excerpt">
            No verbatim excerpt provided in retrieved reference.
          </p>
        )}
      </div>

      {/* Source Provenance Link */}
      {evidence.url && (
        <div className="dossier-provenance-bar">
          <span className="provenance-domain">{hostname || 'External Reference'}</span>
          <a
            href={evidence.url}
            target="_blank"
            rel="noopener noreferrer"
            className="dossier-inspect-btn"
            title={`Inspect original source at ${evidence.url}`}
          >
            <span>INSPECT SOURCE</span>
            <ExternalLinkIcon size={12} />
          </a>
        </div>
      )}
    </article>
  );
};
