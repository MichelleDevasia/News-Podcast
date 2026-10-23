import React, { useState } from 'react';
import type { OptionsResponse } from '../types/options';
import type { NewsRequest } from '../types/news';
import './BriefingForm.css';

interface BriefingFormProps {
  options: OptionsResponse | null;
  loading: boolean;
  onFetchNews: (request: NewsRequest) => void;
  onClose?: () => void;
}

export const BriefingForm: React.FC<BriefingFormProps> = ({
  options,
  loading,
  onFetchNews,
  onClose,
}) => {
  const [country, setCountry] = useState<string>('in');
  const [category, setCategory] = useState<string>('General');
  const [query, setQuery] = useState<string>('');
  const [maxArticles, setMaxArticles] = useState<number>(5);
  const [language, setLanguage] = useState<string>('en');
  const [accent, setAccent] = useState<string>('com');
  const [autoTranslate, setAutoTranslate] = useState<boolean>(true);

  // Form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFetchNews({
      country,
      category,
      query: query.trim() || undefined,
      max_articles: maxArticles,
      language,
      strict_country: true,
      strict_category: true,
      auto_translate: autoTranslate,
    });
  };

  // Estimated duration: ~1.2 to 1.5 minutes per story
  const estimatedMins = Math.max(1, Math.round(maxArticles * 1.3));

  return (
    <section id="briefing-studio" className="briefing-form-section" aria-label="Personalized Briefing Studio">
      <div className="briefing-form-card">
        <div className="form-header">
          <div>
            <div className="form-kicker">CUSTOM PODCAST CREATOR</div>
            <h2 className="form-title">Configure Your Daily Briefing</h2>
            <p className="form-subtitle">
              Choose your destination, subject matter, language, and narration depth.
            </p>
          </div>
          {onClose && (
            <button type="button" className="form-close-btn" onClick={onClose} aria-label="Close studio">
              ✕
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="briefing-grid-form">
          {/* Row 1: Location & Category */}
          <div className="form-field">
            <label htmlFor="country-select" className="field-label">
              <span>🌍 News Location / Edition</span>
            </label>
            <select
              id="country-select"
              className="field-select"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              disabled={loading}
            >
              {options?.countries.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.label}
                </option>
              )) || <option value="in">India (in)</option>}
            </select>
            <span className="field-hint">Filters stories from regional national feeds</span>
          </div>

          <div className="form-field">
            <label htmlFor="category-select" className="field-label">
              <span>📰 News Genre / Category</span>
            </label>
            <select
              id="category-select"
              className="field-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={loading}
            >
              {options?.categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              )) || <option value="General">General</option>}
            </select>
            <span className="field-hint">24 curated domain taxonomies</span>
          </div>

          {/* Row 2: Search Topic & Story Count */}
          <div className="form-field">
            <label htmlFor="query-input" className="field-label">
              <span>🔍 Specific Topic or Keyword (Optional)</span>
            </label>
            <input
              id="query-input"
              type="text"
              className="field-input"
              placeholder="e.g. Artificial Intelligence, Renewable Energy, Markets"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              maxLength={200}
              disabled={loading}
            />
            <span className="field-hint">Matches exact headline and content terms</span>
          </div>

          <div className="form-field">
            <label htmlFor="count-range" className="field-label">
              <span>📊 Number of Stories: <strong>{maxArticles}</strong></span>
            </label>
            <div className="range-container">
              <input
                id="count-range"
                type="range"
                min={2}
                max={15}
                step={1}
                className="field-range"
                value={maxArticles}
                onChange={(e) => setMaxArticles(Number(e.target.value))}
                disabled={loading}
              />
              <div className="duration-indicator">
                <span>⏱️ Est. Episode: ~{estimatedMins} min</span>
              </div>
            </div>
            <span className="field-hint">Duration scales with narrative story length</span>
          </div>

          {/* Row 3: Output Language & Narrator Accent */}
          <div className="form-field">
            <label htmlFor="lang-select" className="field-label">
              <span>🌐 Narration Language</span>
            </label>
            <select
              id="lang-select"
              className="field-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={loading}
            >
              {options?.languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              )) || <option value="en">English</option>}
            </select>
            <span className="field-hint">Automatic NLP translation for non-English briefs</span>
          </div>

          <div className="form-field">
            <label htmlFor="accent-select" className="field-label">
              <span>🎙️ Voice Accent (English)</span>
            </label>
            <select
              id="accent-select"
              className="field-select"
              value={accent}
              onChange={(e) => setAccent(e.target.value)}
              disabled={loading || language !== 'en'}
            >
              {options?.accents.map((a) => (
                <option key={a.tld} value={a.tld}>
                  {a.label}
                </option>
              )) || <option value="com">United States (English)</option>}
            </select>
            <span className="field-hint">Dual hosts alternate accents for natural cadence</span>
          </div>

          {/* Translation Option */}
          <div className="form-field" style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              <input
                type="checkbox"
                checked={autoTranslate}
                onChange={(e) => setAutoTranslate(e.target.checked)}
                disabled={loading}
              />
              <span>Enable automatic neural translation to selected language for briefing</span>
            </label>
          </div>

          {/* Form Actions */}
          <div className="form-actions-full">
            <button
              type="submit"
              className="form-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="btn-spinner"></span>
                  <span>Retrieving Curated Stories...</span>
                </>
              ) : (
                <>
                  <span>Find my stories</span>
                  <span className="btn-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
};
