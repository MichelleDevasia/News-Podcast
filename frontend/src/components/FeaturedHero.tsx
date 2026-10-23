import React from 'react';
import { Globe3D } from './Globe3D';
import type { ArticleItem, MiniArticleItem } from '../types/news';
import './FeaturedHero.css';

interface FeaturedHeroProps {
  theme: 'dark' | 'light';
  articles: ArticleItem[];
  miniArticles: MiniArticleItem[];
  selectedCategory: string;
  onOpenBriefingStudio: () => void;
  onArticleClick?: (article: ArticleItem) => void;
}

export const FeaturedHero: React.FC<FeaturedHeroProps> = ({
  theme,
  articles,
  miniArticles,
  selectedCategory,
  onOpenBriefingStudio,
  onArticleClick,
}) => {
  const leadArticle = articles.length > 0 ? articles[0] : null;
  const secondaryArticles = articles.length > 1
    ? articles.slice(1, 4)
    : miniArticles.slice(0, 3).map((m) => ({
        title: m.title,
        summary: '',
        link: m.link,
        country: '',
        source_id: m.source_id,
        pub_date: m.pub_date,
        score: m.score,
        sentiment: m.sentiment,
      }));

  return (
    <section className="featured-hero-container" aria-label="Featured News and Global Telemetry">
      <div className="featured-hero-grid">
        {/* Left Column: Lead Story & Editorial Brief */}
        <div className="lead-story-col">
          <div className="editorial-kicker">
            <span className="kicker-line" aria-hidden="true"></span>
            <span className="kicker-text">
              {leadArticle ? `FRONT PAGE • ${leadArticle.source_id.toUpperCase()}` : `TOP STORY • ${selectedCategory.toUpperCase()}`}
            </span>
          </div>

          {leadArticle ? (
            <article className="lead-article-card" onClick={() => onArticleClick && onArticleClick(leadArticle)}>
              <h2 className="lead-headline">
                <a href={leadArticle.link} target="_blank" rel="noopener noreferrer">
                  {leadArticle.title}
                </a>
              </h2>
              <p className="lead-summary">{leadArticle.summary}</p>

              <div className="lead-meta">
                <span className="meta-source">{leadArticle.source_id}</span>
                <span className="meta-sep">•</span>
                <span className="meta-date">{leadArticle.pub_date}</span>
                {leadArticle.sentiment && (
                  <>
                    <span className="meta-sep">•</span>
                    <span className={`meta-sentiment ${leadArticle.sentiment.toLowerCase()}`}>
                      {leadArticle.sentiment}
                    </span>
                  </>
                )}
              </div>
            </article>
          ) : (
            <div className="lead-intro-block">
              <h2 className="lead-headline">
                Global news.<br />
                <span className="editorial-accent">Audio briefings.</span>
              </h2>
              <p className="lead-summary">
                Curated from trusted international reporting and transformed into natural, conversational dual-host podcasts in your chosen language.
              </p>
            </div>
          )}

          {/* Prominent Briefing Entry Point */}
          <div className="hero-action-block">
            <button
              type="button"
              className="editorial-cta-btn"
              onClick={onOpenBriefingStudio}
            >
              <span>Create your briefing</span>
              <span className="btn-arrow" aria-hidden="true">→</span>
            </button>
            <span className="hero-trust-badge">
              <span className="check-mark">✓</span> Powered by real-time NLP & gTTS
            </span>
          </div>

          {/* Secondary Editorial Stories / Quick Dispatch */}
          {secondaryArticles.length > 0 && (
            <div className="secondary-stories-strip">
              <h3 className="secondary-title">Developing Dispatches</h3>
              <ul className="secondary-list">
                {secondaryArticles.map((art, idx) => (
                  <li key={idx} className="secondary-item">
                    <a href={art.link} target="_blank" rel="noopener noreferrer" className="secondary-link">
                      <span className="secondary-num">{idx + 1}.</span>
                      <span className="secondary-headline">{art.title}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Right Column: Genuine 3D Rotating Globe */}
        <div className="globe-col">
          <div className="globe-frame">
            <div className="globe-editorial-caption">
              <span className="caption-dot"></span>
              <span>Global Telemetry & Active Bureau Network</span>
            </div>

            <Globe3D theme={theme} />
          </div>
        </div>
      </div>
    </section>
  );
};
