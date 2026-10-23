import React from 'react';
import './Masthead.css';

interface MastheadProps {
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  apiConnected: boolean | null;
  onNavigateHome: () => void;
}

export const Masthead: React.FC<MastheadProps> = ({
  theme,
  onToggleTheme,
  apiConnected,
  onNavigateHome,
}) => {
  // Format current date in newspaper style
  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date());

  return (
    <header className="masthead-container" role="banner">
      {/* Top Utility Bar: Date, Edition, Health Status, Theme Switcher */}
      <div className="masthead-topbar">
        <div className="masthead-date">
          <span>{todayFormatted}</span>
          <span className="dot-sep">•</span>
          <span className="edition-tag">International Audio Edition</span>
        </div>

        <div className="masthead-utils">
          {/* Real Backend Connection Indicator */}
          <div
            className={`masthead-health ${apiConnected === true ? 'connected' : apiConnected === false ? 'error' : 'pending'}`}
            title={apiConnected === true ? 'Connected to FastAPI Backend (Port 8001)' : 'Connecting to API...'}
          >
            <span className="health-dot"></span>
            <span className="health-text">
              {apiConnected === true ? 'API Live' : apiConnected === false ? 'API Offline' : 'Connecting...'}
            </span>
          </div>

          <span className="dot-sep">•</span>

          {/* Theme Toggle Button */}
          <button
            type="button"
            className="masthead-theme-btn"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            <span className="theme-emoji" aria-hidden="true">
              {theme === 'dark' ? '☀️' : '🌙'}
            </span>
            <span className="theme-text">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        </div>
      </div>

      {/* Main Newspaper Masthead */}
      <div className="masthead-main">
        <div className="masthead-emblem-left" aria-hidden="true">
          <span className="audio-symbol">🎙️</span>
        </div>

        <div className="masthead-title-wrap" onClick={onNavigateHome} role="button" tabIndex={0}>
          <h1 className="masthead-title">NEWS PODCAST</h1>
          <p className="masthead-tagline">The world, in your words.</p>
        </div>

        <div className="masthead-emblem-right" aria-hidden="true">
          <span className="audio-symbol">📻</span>
        </div>
      </div>
    </header>
  );
};
