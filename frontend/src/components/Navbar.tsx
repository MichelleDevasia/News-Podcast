import React from 'react';
import './Navbar.css';

interface NavbarProps {
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  apiConnected: boolean | null;
  onNavigateSection?: (section: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  theme,
  onToggleTheme,
  apiConnected,
  onNavigateSection,
}) => {
  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, section: string) => {
    e.preventDefault();
    if (onNavigateSection) {
      onNavigateSection(section);
    }
  };

  return (
    <header className="navbar-container" role="banner">
      <div className="navbar-content">
        {/* Brand */}
        <div className="navbar-brand">
          <span className="brand-icon" aria-hidden="true">🎙️</span>
          <span className="brand-name">News Podcast</span>
        </div>

        {/* Navigation Links */}
        <nav className="navbar-links" aria-label="Main Navigation">
          <a
            href="#home"
            className="nav-link active"
            onClick={(e) => handleNavClick(e, 'home')}
          >
            Home
          </a>
          <a
            href="#about"
            className="nav-link"
            onClick={(e) => handleNavClick(e, 'about')}
          >
            About
          </a>
          <a
            href="#help"
            className="nav-link"
            onClick={(e) => handleNavClick(e, 'help')}
          >
            Help
          </a>
        </nav>

        {/* Right Controls: Health Status & Theme Toggle */}
        <div className="navbar-actions">
          {/* Real Backend Connection Indicator */}
          <div
            className={`api-indicator ${apiConnected === true ? 'connected' : apiConnected === false ? 'error' : 'pending'}`}
            title={apiConnected === true ? 'FastAPI Backend Connected (/api/health)' : 'Backend health check pending'}
            aria-live="polite"
          >
            <span className="indicator-dot"></span>
            <span className="indicator-label">
              {apiConnected === true ? 'API Connected' : apiConnected === false ? 'API Offline' : 'Connecting...'}
            </span>
          </div>

          {/* Theme Toggle Button */}
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <span className="theme-icon" aria-hidden="true">☀️</span>
            ) : (
              <span className="theme-icon" aria-hidden="true">🌙</span>
            )}
            <span className="theme-label">{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
