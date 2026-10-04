import React from 'react';
import {
  FileTextIcon,
  SearchIcon,
  DatabaseIcon,
  GlobeIcon,
  GitBranchIcon,
  ShieldIcon,
  CheckCircleIcon,
} from '../common/Icons';

export interface PipelineStage {
  id: string;
  step: string;
  name: string;
  description: string;
  icon: React.FC<{ size?: number; className?: string }>;
}

export const PIPELINE_STAGES: PipelineStage[] = [
  {
    id: 'article',
    step: '01',
    name: 'ARTICLE',
    description: 'Ingest raw article URL & parse text structure',
    icon: FileTextIcon,
  },
  {
    id: 'claim',
    step: '02',
    name: 'CLAIM',
    description: 'Isolate central verifiable factual assertion',
    icon: SearchIcon,
  },
  {
    id: 'factchecks',
    step: '03',
    name: 'FACT-CHECKS',
    description: 'Query trusted fact-checking databases',
    icon: DatabaseIcon,
  },
  {
    id: 'sources',
    step: '04',
    name: 'SOURCES',
    description: 'Retrieve independent corroborating reports',
    icon: GlobeIcon,
  },
  {
    id: 'evidence',
    step: '05',
    name: 'EVIDENCE',
    description: 'Extract supporting vs. contradicting findings',
    icon: GitBranchIcon,
  },
  {
    id: 'analysis',
    step: '06',
    name: 'ANALYSIS',
    description: 'Synthesize transparent contextual reasoning',
    icon: ShieldIcon,
  },
  {
    id: 'result',
    step: '07',
    name: 'RESULT',
    description: 'Present traceable dossier & source links',
    icon: CheckCircleIcon,
  },
];

interface VerificationPipelineProps {
  mode?: 'overview' | 'processing' | 'completed';
  compact?: boolean;
}

export const VerificationPipeline: React.FC<VerificationPipelineProps> = ({
  mode = 'overview',
  compact = false,
}) => {
  return (
    <div
      className={`pipeline-container pipeline-mode-${mode} ${
        compact ? 'pipeline-compact' : ''
      }`}
      aria-label="VERITO 7-Stage Verification Pipeline"
    >
      <div className="pipeline-header-bar">
        <div className="pipeline-title-group">
          <span className="pipeline-telemetry-tag">
            SYS//PIPELINE &bull; 7-NODE VERIFICATION ARCHITECTURE
          </span>
          <span className="pipeline-mode-badge">
            {mode === 'processing' && 'INSPECTION ACTIVE &bull; SCANNING'}
            {mode === 'completed' && 'PIPELINE DISPATCH &bull; TRACE ASSEMBLED'}
            {mode === 'overview' && 'SYSTEM PROTOCOL &bull; EVIDENCE-DRIVEN'}
          </span>
        </div>
      </div>

      <div className="pipeline-track">
        {PIPELINE_STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isLast = idx === PIPELINE_STAGES.length - 1;

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`pipeline-node ${
                  mode === 'completed' ? 'node-completed' : ''
                } ${mode === 'processing' ? 'node-processing' : ''}`}
                style={{ animationDelay: `${idx * 0.15}s` }}
              >
                <div className="node-icon-wrapper">
                  <Icon size={16} className="node-icon" />
                  <span className="node-step-tag">{stage.step}</span>
                </div>
                <div className="node-info">
                  <span className="node-name">{stage.name}</span>
                  {!compact && (
                    <span className="node-desc">{stage.description}</span>
                  )}
                </div>
                {mode === 'processing' && <span className="node-scan-sweep" />}
              </div>

              {!isLast && (
                <div className="pipeline-connector" aria-hidden="true">
                  <span className="connector-line" />
                  <span className="connector-node-dot" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
