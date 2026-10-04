import React from 'react';
import type { SourceItem } from '../../types/verification';
import { ExternalLinkIcon, GlobeIcon, DatabaseIcon } from '../common/Icons';

interface SourcesSectionProps {
  sources?: (SourceItem | string)[];
}

export const SourcesSection: React.FC<SourcesSectionProps> = ({ sources = [] }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  // Normalize sources gracefully (handles both string URLs and SourceItem objects)
  const normalizedSources: SourceItem[] = sources.map((item) => {
    if (typeof item === 'string') {
      let hostname = '';
      try {
        hostname = new URL(item).hostname.replace(/^www\./, '');
      } catch {
        hostname = 'External Web Source';
      }
      return {
        url: item,
        source: hostname,
        title: item,
      };
    }
    return item;
  });

  return (
    <section className="source-trace-section" aria-labelledby="sources-heading">
      {/* Header */}
      <div className="source-trace-header">
        <div className="trace-header-left">
          <DatabaseIcon size={16} className="trace-header-icon" />
          <h3 id="sources-heading" className="trace-main-title">
            PROVENANCE &amp; SOURCE TRACE MATRIX
          </h3>
        </div>
        <div className="trace-header-right">
          <span className="trace-count-chip">
            {normalizedSources.length} {normalizedSources.length === 1 ? 'CONSULTED SOURCE' : 'CONSULTED SOURCES'}
          </span>
        </div>
      </div>

      <p className="source-trace-caption">
        All conclusions are linked directly to verifiable external records. You can inspect the primary references below:
      </p>

      {/* Grid of Indexed Source Cards */}
      <div className="source-trace-grid">
        {normalizedSources.map((source, index) => {
          const indexTag = `[${String(index + 1).padStart(2, '0')}]`;

          let domain = source.source;
          if (!domain && source.url) {
            try {
              domain = new URL(source.url).hostname.replace(/^www\./, '');
            } catch {
              domain = 'External Source';
            }
          }

          return (
            <div key={`source-trace-${index}`} className="trace-source-card">
              <div className="trace-card-top">
                <div className="trace-index-badge">{indexTag} SOURCE</div>
                <div className="trace-domain-tag">
                  <GlobeIcon size={12} className="trace-globe-icon" />
                  <span>{domain || 'Independent Publisher'}</span>
                </div>
              </div>

              {source.title && source.title !== source.url && (
                <h4 className="trace-card-title">{source.title}</h4>
              )}

              {source.description && (
                <p className="trace-card-description">{source.description}</p>
              )}

              {source.url && (
                <div className="trace-card-action">
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="trace-url-btn"
                    title={`Open verified reference: ${source.url}`}
                  >
                    <span className="trace-url-label">{source.url}</span>
                    <ExternalLinkIcon size={12} className="trace-link-arrow" />
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};
