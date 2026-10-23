import { useState, useEffect, useCallback, useRef } from 'react';
import { Masthead } from './components/Masthead';
import { CategoryNav } from './components/CategoryNav';
import { FeaturedHero } from './components/FeaturedHero';
import { BriefingForm } from './components/BriefingForm';
import { NewsSection } from './components/NewsSection';
import { PodcastPlayer } from './components/PodcastPlayer';
import { StatsStrip } from './components/StatsStrip';
import { getOptions, getHealth, fetchNews, generatePodcastAudio } from './services/api';
import type { OptionsResponse } from './types/options';
import type { NewsRequest, NewsResponse, PodcastRequest } from './types/news';
import './App.css';

function getInitialTheme(): 'dark' | 'light' {
  const saved = localStorage.getItem('news_podcast_theme');
  if (saved === 'dark' || saved === 'light') {
    return saved;
  }
  if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light';
  }
  return 'dark';
}

function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>(getInitialTheme);
  const [options, setOptions] = useState<OptionsResponse | null>(null);
  const [loadingOptions, setLoadingOptions] = useState<boolean>(true);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);

  // Briefing form & News state
  const [selectedCategory, setSelectedCategory] = useState<string>('General');
  const [showStudio, setShowStudio] = useState<boolean>(false);
  const [loadingNews, setLoadingNews] = useState<boolean>(false);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<NewsResponse | null>(null);
  const [currentRequest, setCurrentRequest] = useState<NewsRequest | null>(null);

  // Podcast audio state
  const [loadingPodcast, setLoadingPodcast] = useState<boolean>(false);
  const [podcastError, setPodcastError] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const studioRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<HTMLDivElement>(null);

  // Apply data-theme attribute and save to localStorage
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('news_podcast_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Check backend health
  const checkHealthStatus = useCallback(async () => {
    try {
      const health = await getHealth();
      setApiConnected(health.status === 'healthy');
    } catch {
      setApiConnected(false);
    }
  }, []);

  // Fetch configuration options
  const loadOptions = useCallback(async () => {
    setLoadingOptions(true);
    setOptionsError(null);
    try {
      const data = await getOptions();
      setOptions(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend';
      setOptionsError(message);
    } finally {
      setLoadingOptions(false);
    }
  }, []);

  useEffect(() => {
    checkHealthStatus();
    loadOptions();
  }, [checkHealthStatus, loadOptions]);

  // Open Briefing Studio
  const handleOpenStudio = () => {
    setShowStudio(true);
    setTimeout(() => {
      studioRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // Select Category from Header Navigation
  const handleSelectCategory = async (category: string) => {
    setSelectedCategory(category);
    // Fetch news for this category automatically
    const request: NewsRequest = {
      country: 'in',
      category: category,
      max_articles: 5,
      language: 'en',
      strict_country: true,
      strict_category: true,
      auto_translate: true,
    };
    handleFetchNews(request);
  };

  // Fetch News from Backend
  const handleFetchNews = async (request: NewsRequest) => {
    setLoadingNews(true);
    setNewsError(null);
    setCurrentRequest(request);
    setSelectedCategory(request.category);
    setAudioBlob(null); // Reset existing audio when new news is fetched

    try {
      const result = await fetchNews(request);
      setNewsData(result);
      // Scroll to news results after brief pause
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 150);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve news from backend';
      setNewsError(msg);
    } finally {
      setLoadingNews(false);
    }
  };

  // Generate Podcast Audio from Real Articles
  const handleGeneratePodcast = async () => {
    if (!newsData || !currentRequest) return;

    setLoadingPodcast(true);
    setPodcastError(null);

    const podcastReq: PodcastRequest = {
      category: newsData.category,
      language: currentRequest.language || 'en',
      accent: 'com',
      main_articles: newsData.main_articles.map((a) => ({
        title: a.title,
        summary: a.summary,
      })),
      mini_articles: newsData.mini_articles.map((m) => ({
        title: m.title,
      })),
    };

    try {
      const blob = await generatePodcastAudio(podcastReq);
      setAudioBlob(blob);
      setTimeout(() => {
        playerRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 150);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to generate podcast audio';
      setPodcastError(msg);
    } finally {
      setLoadingPodcast(false);
    }
  };

  return (
    <div className="page-wrapper">
      {/* Newspaper Masthead */}
      <Masthead
        theme={theme}
        onToggleTheme={toggleTheme}
        apiConnected={apiConnected}
        onNavigateHome={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      />

      {/* Horizontal News Category Navigation */}
      <CategoryNav
        categories={options?.categories || []}
        selectedCategory={selectedCategory}
        onSelectCategory={handleSelectCategory}
        onOpenBriefingStudio={handleOpenStudio}
      />

      {/* Main Editorial Hero Section with 3D Globe */}
      <FeaturedHero
        theme={theme}
        articles={newsData?.main_articles || []}
        miniArticles={newsData?.mini_articles || []}
        selectedCategory={selectedCategory}
        onOpenBriefingStudio={handleOpenStudio}
      />

      {/* Live Configuration Statistics Strip */}
      <StatsStrip
        options={options}
        loading={loadingOptions}
        error={optionsError}
        onRetry={loadOptions}
      />

      {/* Briefing Studio / Preferences Form */}
      {(showStudio || !newsData) && (
        <div ref={studioRef}>
          <BriefingForm
            options={options}
            loading={loadingNews}
            onFetchNews={handleFetchNews}
            onClose={() => setShowStudio(false)}
          />
        </div>
      )}

      {/* Error Banner for News Retrieval */}
      {newsError && (
        <div className="app-error-banner" role="alert">
          <span className="error-icon">⚠️</span>
          <div className="error-details">
            <strong>News Retrieval Notice:</strong> {newsError}
          </div>
          {currentRequest && (
            <button
              type="button"
              className="error-retry-btn"
              onClick={() => handleFetchNews(currentRequest)}
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* Error Banner for Podcast Generation */}
      {podcastError && (
        <div className="app-error-banner" role="alert">
          <span className="error-icon">⚠️</span>
          <div className="error-details">
            <strong>Podcast Audio Notice:</strong> {podcastError}
          </div>
          <button
            type="button"
            className="error-retry-btn"
            onClick={handleGeneratePodcast}
          >
            Retry Generation
          </button>
        </div>
      )}

      {/* News Results Section */}
      {newsData && (
        <div ref={resultsRef}>
          <NewsSection
            newsData={newsData}
            loadingPodcast={loadingPodcast}
            onGeneratePodcast={handleGeneratePodcast}
          />
        </div>
      )}

      {/* Dedicated Podcast Audio Player & Included Stories */}
      {audioBlob && newsData && (
        <div ref={playerRef}>
          <PodcastPlayer
            audioBlob={audioBlob}
            category={newsData.category}
            language={currentRequest?.language || 'en'}
            mainArticles={newsData.main_articles}
            miniArticles={newsData.mini_articles}
            onBackToNews={() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' })}
            onNewBriefing={handleOpenStudio}
          />
        </div>
      )}

      {/* Informative "How It Works" Section */}
      <section className="preview-section" aria-label="How News Podcast Works">
        <div className="preview-container">
          <div className="section-header">
            <span className="section-label">EDITORIAL WORKFLOW</span>
            <h2 className="section-title">From Global Reporting to Conversational Audio</h2>
            <p className="section-desc">
              How our data science and audio pipeline curates and synthesizes personalized briefings.
            </p>
          </div>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-num">01</div>
              <h3 className="step-title">Multi-Source Wire Retrieval</h3>
              <p className="step-text">
                Live international dispatches fetched across {options?.countries.length || 11} national editions with automatic RSS fallback.
              </p>
            </div>

            <div className="step-card">
              <div className="step-num">02</div>
              <h3 className="step-title">NLP Scoring & Deduplication</h3>
              <p className="step-text">
                Cosine similarity clustering and sentiment scoring rank the most critical reporting without repetitive duplicates.
              </p>
            </div>

            <div className="step-card">
              <div className="step-num">03</div>
              <h3 className="step-title">Dual-Host Audio Synthesis</h3>
              <p className="step-text">
                Conversational script generation with alternating narrator accents and multilingual gTTS translation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Newspaper Footer */}
      <footer className="footer-container" role="contentinfo">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="footer-icon">🎙️</span>
            <span>News Podcast</span>
            <span className="footer-divider">•</span>
            <span className="footer-tagline">The world, in your words.</span>
          </div>

          <div className="footer-meta">
            <span>FastAPI Backend (Port 8001)</span>
            <span className="footer-divider">•</span>
            <span>React + TypeScript + Three.js</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
