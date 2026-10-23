import React from 'react';
import type { NewsResponse } from '../types/news';
import './NewsSection.css';

interface NewsSectionProps {
  newsData: NewsResponse;
  loadingPodcast: boolean;
  onGeneratePodcast: () => void;
}

export const NewsSection: React.FC<NewsSectionProps> = ({
  newsData,
  loadingPodcast,
  onGeneratePodcast,
}) => {
  const { main_articles, mini_articles, category, country, source, sentiment_summary } = newsData;

  const totalArticles = main_articles.length + mini_articles.length;

  if (totalArticles === 0) {
    return (
      <section className="news-section-container" aria-label="News Results">
        <div className="news-empty-card">
          <div className="empty-icon">📰</div>
          <h3>No Articles Found</h3>
          <p>
            No stories matched your specific filter combination. Try selecting a broader category like
            "General" or clearing the keyword query.
          </p>
        </div>
      </section>
    );
  }

  const leadArticle = main_articles[0];
  const secondaryArticles = main_articles.slice(1);

  return (
    <section id="news-results" className="news-section-container" aria-label="Curated News Stories">
      {/* Editorial Section Header */}
      <div className="news-section-header">
        <div>
          <div className="section-edition-tag">
            <span>CURATED DISPATCH • {country.toUpperCase()}</span>
            <span className="source-badge-indicator">
              {source === 'newsdata' ? 'NewsData.io Wire' : 'Google News RSS Wire'}
            </span>
          </div>
          <h2 className="news-section-title">
            Latest Reporting: {category}
          </h2>
          <p className="news-section-subtitle">
            {totalArticles} articles verified and ranked by importance, recency, and editorial weight.
          </p>
        </div>

        {/* Primary Action to Generate Podcast */}
        <div className="podcast-trigger-wrap">
          <button
            type="button"
            className="generate-podcast-btn"
            onClick={onGeneratePodcast}
            disabled={loadingPodcast}
          >
            {loadingPodcast ? (
              <>
                <span className="podcast-btn-spinner"></span>
                <span>Synthesizing Podcast Audio...</span>
              </>
            ) : (
              <>
                <span className="mic-icon" aria-hidden="true">🎙️</span>
                <span>Generate Podcast ({totalArticles} stories)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Sentiment Summary Bar */}
      <div className="sentiment-strip">
        <span className="sentiment-strip-title">Sentiment Distribution:</span>
        <div className="sentiment-tags">
          <span className="sentiment-tag positive">
            🙂 Positive: {sentiment_summary.positive}
          </span>
          <span className="sentiment-tag neutral">
            😐 Neutral: {sentiment_summary.neutral}
          </span>
          <span className="sentiment-tag negative">
            🙁 Negative: {sentiment_summary.negative}
          </span>
        </div>
      </div>

      {/* Newspaper Multi-Column Layout */}
      <div className="newspaper-articles-grid">
        {/* Featured Top Story */}
        {leadArticle && (
          <article className="lead-newspaper-article">
            <div className="article-badge-bar">
              <span className="article-badge badge-cat">{category}</span>
              <span className="article-badge badge-source">{leadArticle.source_id}</span>
              <span className="article-badge badge-score">Match Score: {leadArticle.score}</span>
            </div>

            <h3 className="lead-article-headline">
              <a href={leadArticle.link} target="_blank" rel="noopener noreferrer">
                {leadArticle.title}
              </a>
            </h3>

            <p className="lead-article-summary">{leadArticle.summary}</p>

            <div className="article-footer">
              <span className="article-date">📅 {leadArticle.pub_date}</span>
              {leadArticle.link && leadArticle.link !== '#' && (
                <a
                  href={leadArticle.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="article-source-link"
                >
                  Read original reporting ↗
                </a>
              )}
            </div>
          </article>
        )}

        {/* Secondary Stories Grid */}
        <div className="secondary-articles-column">
          {secondaryArticles.map((art, idx) => (
            <article key={idx} className="secondary-newspaper-article">
              <div className="article-badge-bar">
                <span className="article-badge badge-source">{art.source_id}</span>
                <span className="article-badge badge-score">Score: {art.score}</span>
              </div>

              <h4 className="secondary-article-headline">
                <a href={art.link} target="_blank" rel="noopener noreferrer">
                  {art.title}
                </a>
              </h4>

              <p className="secondary-article-summary">{art.summary}</p>

              <div className="article-footer">
                <span className="article-date">{art.pub_date}</span>
                {art.link && art.link !== '#' && (
                  <a
                    href={art.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="article-source-link"
                  >
                    Original link ↗
                  </a>
                )}
              </div>
            </article>
          ))}
        </div>
      </div>

      {/* Mini Bulletins Strip (Quick Updates) */}
      {mini_articles.length > 0 && (
        <div className="mini-bulletins-container">
          <div className="bulletins-header">
            <span className="flash-icon">⚡</span>
            <h3>Quick News Bulletins</h3>
          </div>
          <div className="bulletins-grid">
            {mini_articles.map((mini, idx) => (
              <div key={idx} className="mini-bulletin-item">
                <span className="bulletin-bullet">•</span>
                <div className="bulletin-content">
                  <a href={mini.link} target="_blank" rel="noopener noreferrer" className="bulletin-headline">
                    {mini.title}
                  </a>
                  <span className="bulletin-meta">
                    {mini.source_id} • Score: {mini.score}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom CTA */}
      <div className="news-bottom-cta">
        <button
          type="button"
          className="generate-podcast-btn bottom-btn"
          onClick={onGeneratePodcast}
          disabled={loadingPodcast}
        >
          {loadingPodcast ? (
            <>
              <span className="podcast-btn-spinner"></span>
              <span>Synthesizing Podcast Audio...</span>
            </>
          ) : (
            <>
              <span className="mic-icon" aria-hidden="true">🎙️</span>
              <span>Listen to this Briefing as a Podcast</span>
            </>
          )}
        </button>
      </div>
    </section>
  );
};
