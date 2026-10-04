import React, { useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { VerificationHero } from './components/verification/VerificationHero';
import { UrlInput } from './components/verification/UrlInput';
import { VerificationPipeline } from './components/verification/VerificationPipeline';
import { LoadingState } from './components/verification/LoadingState';
import { ResultsView } from './components/verification/ResultsView';
import { ErrorState } from './components/verification/ErrorState';
import { verifyArticle, ApiError } from './services/api';
import type { VerifyResponse, VerificationError, VerificationViewStatus } from './types/verification';
import {
  FileTextIcon,
  GlobeIcon,
  GitBranchIcon,
  ShieldIcon,
  TerminalIcon,
} from './components/common/Icons';

export const App: React.FC = () => {
  const [viewStatus, setViewStatus] = useState<VerificationViewStatus>('idle');
  const [currentUrl, setCurrentUrl] = useState<string>('');
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<VerificationError | null>(null);

  const handleVerify = async (url: string) => {
    setCurrentUrl(url);
    setViewStatus('loading');
    setError(null);

    try {
      const response = await verifyArticle(url);
      setResult(response);
      setViewStatus('results');
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.structuredError);
      } else {
        setError({
          title: 'Investigation Probe Exception',
          message:
            err instanceof Error
              ? err.message
              : 'An unexpected exception occurred during the verification probe.',
          technicalDetails: String(err),
          actionSuggestion: 'Check server connectivity and verify the target article URL.',
        });
      }
      setViewStatus('error');
    }
  };

  const handleRetry = () => {
    if (currentUrl) {
      handleVerify(currentUrl);
    } else {
      setViewStatus('idle');
    }
  };

  const handleReset = () => {
    setViewStatus('idle');
    setResult(null);
    setError(null);
  };

  const handleEditUrl = () => {
    setViewStatus('idle');
  };

  return (
    <div className="console-app-shell">
      {/* Background Matrix/Grid Elements */}
      <div className="cyber-grid-overlay" aria-hidden="true" />
      <div className="cyber-crosshair crosshair-top-left hide-mobile" aria-hidden="true">+</div>
      <div className="cyber-crosshair crosshair-top-right hide-mobile" aria-hidden="true">+</div>

      <Navbar onReset={handleReset} />

      <main className="console-main-content">
        <div className="container">
          {/* IDLE / INVESTIGATION COMMAND VIEW */}
          {viewStatus === 'idle' && (
            <div className="home-investigation-view">
              <VerificationHero />

              <UrlInput
                initialUrl={currentUrl}
                isLoading={false}
                onVerify={handleVerify}
              />

              {/* 7-Stage Architectural Pipeline Display */}
              <div className="signature-pipeline-section">
                <VerificationPipeline mode="overview" />
              </div>

              {/* Forensic Methodology Grid */}
              <section className="methodology-matrix-section">
                <div className="matrix-title-bar">
                  <TerminalIcon size={14} className="matrix-icon" />
                  <span className="matrix-heading">
                    SYSTEM METHODOLOGY &bull; EVIDENCE-DRIVEN RESEARCH PROTOCOL
                  </span>
                </div>

                <div className="methodology-cards-grid">
                  <div className="methodology-card">
                    <div className="methodology-card-header">
                      <FileTextIcon size={16} className="card-icon" />
                      <span className="card-step-id">01 // ISOLATE</span>
                    </div>
                    <h4 className="card-title">Claim Deconstruction</h4>
                    <p className="card-body">
                      Extracts the primary verifiable assertion from the article rather than treating opinion as fact.
                    </p>
                  </div>

                  <div className="methodology-card">
                    <div className="methodology-card-header">
                      <GlobeIcon size={16} className="card-icon" />
                      <span className="card-step-id">02 // RETRIEVE</span>
                    </div>
                    <h4 className="card-title">Multi-Index Search</h4>
                    <p className="card-body">
                      Cross-references authoritative fact-checking archives, news databases, and scientific records.
                    </p>
                  </div>

                  <div className="methodology-card">
                    <div className="methodology-card-header">
                      <GitBranchIcon size={16} className="card-icon" />
                      <span className="card-step-id">03 // CONTRAST</span>
                    </div>
                    <h4 className="card-title">Bifurcated Stance</h4>
                    <p className="card-body">
                      Maps retrieved findings into explicit supporting versus contradicting evidence categories.
                    </p>
                  </div>

                  <div className="methodology-card">
                    <div className="methodology-card-header">
                      <ShieldIcon size={16} className="card-icon" />
                      <span className="card-step-id">04 // SYNTHESIZE</span>
                    </div>
                    <h4 className="card-title">Traceable Reasoning</h4>
                    <p className="card-body">
                      Produces transparent logical synthesis with direct source provenance. No unexplained percentages.
                    </p>
                  </div>
                </div>
              </section>
            </div>
          )}

          {/* LOADING / PROBE VIEW */}
          {viewStatus === 'loading' && (
            <div className="loading-investigation-view">
              <LoadingState url={currentUrl} />
            </div>
          )}

          {/* RESULTS / INVESTIGATION DOSSIER VIEW */}
          {viewStatus === 'results' && result && (
            <ResultsView
              result={result}
              originalUrl={currentUrl}
              onNewVerification={handleReset}
            />
          )}

          {/* ERROR / DIAGNOSTIC VIEW */}
          {viewStatus === 'error' && error && (
            <div className="error-investigation-view">
              <div className="error-input-frame">
                <UrlInput
                  initialUrl={currentUrl}
                  isLoading={false}
                  onVerify={handleVerify}
                />
              </div>

              <ErrorState
                error={error}
                onRetry={handleRetry}
                onEditUrl={handleEditUrl}
              />
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default App;
