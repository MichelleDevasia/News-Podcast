import React from 'react';
import type { OptionsResponse } from '../types/options';
import './StatsStrip.css';

interface StatsStripProps {
  options: OptionsResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export const StatsStrip: React.FC<StatsStripProps> = ({
  options,
  loading,
  error,
  onRetry,
}) => {
  return (
    <section className="stats-strip-container" aria-label="Global Coverage Statistics">
      <div className="stats-strip-inner">
        {loading && (
          <div className="stats-loading">
            <span className="stats-spinner"></span>
            <span>Fetching live catalog statistics from backend...</span>
          </div>
        )}

        {error && !loading && (
          <div className="stats-error">
            <span>Unable to retrieve configuration metrics ({error})</span>
            <button type="button" className="stats-retry-btn" onClick={onRetry}>
              Retry
            </button>
          </div>
        )}

        {options && !loading && !error && (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-number">{options.categories.length}</span>
              <span className="stat-label">News Categories</span>
              <span className="stat-sub">Curated domain genres</span>
            </div>

            <div className="stat-divider" aria-hidden="true"></div>

            <div className="stat-card">
              <span className="stat-number">{options.countries.length}</span>
              <span className="stat-label">Global Editions</span>
              <span className="stat-sub">Regional news bureaus</span>
            </div>

            <div className="stat-divider" aria-hidden="true"></div>

            <div className="stat-card">
              <span className="stat-number">{options.languages.length}</span>
              <span className="stat-label">Listening Languages</span>
              <span className="stat-sub">Multilingual narration</span>
            </div>

            <div className="stat-divider" aria-hidden="true"></div>

            <div className="stat-card">
              <span className="stat-number">{options.accents.length}</span>
              <span className="stat-label">Narrator Accents</span>
              <span className="stat-sub">Dual-host voice modulation</span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
