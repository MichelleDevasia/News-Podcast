import React, { useState, useRef, useEffect } from 'react';
import type { ArticleItem, MiniArticleItem } from '../types/news';
import './PodcastPlayer.css';

interface PodcastPlayerProps {
  audioBlob: Blob;
  category: string;
  language: string;
  mainArticles: ArticleItem[];
  miniArticles: MiniArticleItem[];
  onBackToNews: () => void;
  onNewBriefing: () => void;
}

export const PodcastPlayer: React.FC<PodcastPlayerProps> = ({
  audioBlob,
  category,
  language,
  mainArticles,
  miniArticles,
  onBackToNews,
  onNewBriefing,
}) => {
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [volume, setVolume] = useState<number>(1);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Manage in-memory Object URL and properly revoke on unmount or change
  useEffect(() => {
    const url = URL.createObjectURL(audioBlob);
    setAudioUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [audioBlob]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => console.error('Audio play failed:', err));
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = Number(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setVolume(val);
    if (audioRef.current) {
      audioRef.current.volume = val;
    }
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const totalStories = mainArticles.length + miniArticles.length;

  return (
    <section id="podcast-player" className="podcast-player-section" aria-label="Podcast Audio Player">
      <div className="player-card">
        {/* Hidden native audio tag */}
        {audioUrl && (
          <audio
            ref={audioRef}
            src={audioUrl}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />
        )}

        {/* Player Header */}
        <div className="player-top-header">
          <div className="player-badge">
            <span className="live-pulse-dot"></span>
            <span>CUSTOM AUDIO BRIEFING READY</span>
          </div>

          <div className="player-top-actions">
            <button type="button" className="action-pill-btn" onClick={onBackToNews}>
              ← Back to Stories
            </button>
            <button type="button" className="action-pill-btn primary" onClick={onNewBriefing}>
              ⚙️ New Briefing
            </button>
          </div>
        </div>

        {/* Title Block */}
        <div className="player-meta-block">
          <h2 className="podcast-episode-title">
            🎙️ Daily {category} News Briefing
          </h2>
          <p className="podcast-episode-sub">
            Dual-host conversational briefing covering {totalStories} verified news stories ({language.toUpperCase()} Narration)
          </p>
        </div>

        {/* Custom Audio Control Bar */}
        <div className="audio-control-deck">
          {/* Play/Pause Button */}
          <button
            type="button"
            className="play-pause-btn"
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pause podcast' : 'Play podcast'}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          {/* Time & Progress */}
          <div className="time-scrubber-group">
            <span className="time-display">{formatTime(currentTime)}</span>
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={handleSeek}
              className="audio-seekbar"
              aria-label="Audio progress slider"
            />
            <span className="time-display">{formatTime(duration)}</span>
          </div>

          {/* Volume Control */}
          <div className="volume-group">
            <span className="vol-icon" aria-hidden="true">🔊</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={handleVolumeChange}
              className="volume-slider"
              aria-label="Volume slider"
            />
          </div>

          {/* Download MP3 */}
          {audioUrl && (
            <a
              href={audioUrl}
              download={`news_podcast_${category.toLowerCase().replace(/\s+/g, '_')}.mp3`}
              className="download-mp3-btn"
              title="Download MP3 file"
            >
              <span>💾 Download MP3</span>
            </a>
          )}
        </div>

        {/* Included Stories Section */}
        <div className="included-stories-panel">
          <div className="panel-header">
            <h3>Stories Included in this Episode ({totalStories})</h3>
            <span className="attribution-note">
              Summaries generated by News Podcast NLP • Click links below to read publisher reporting
            </span>
          </div>

          <div className="included-stories-list">
            {mainArticles.map((art, idx) => (
              <div key={idx} className="included-story-item">
                <span className="story-idx">{idx + 1}.</span>
                <div className="story-details">
                  <div className="story-title-row">
                    <h4 className="story-headline">{art.title}</h4>
                    <span className="story-source-badge">{art.source_id}</span>
                  </div>
                  <p className="story-snippet">{art.summary}</p>
                  {art.link && art.link !== '#' && (
                    <a
                      href={art.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="story-publisher-link"
                    >
                      Read original article on {art.source_id} ↗
                    </a>
                  )}
                </div>
              </div>
            ))}

            {miniArticles.map((mini, idx) => (
              <div key={`mini-${idx}`} className="included-story-item mini-item">
                <span className="story-idx">•</span>
                <div className="story-details">
                  <div className="story-title-row">
                    <h4 className="story-headline">{mini.title}</h4>
                    <span className="story-source-badge">{mini.source_id}</span>
                  </div>
                  {mini.link && mini.link !== '#' && (
                    <a
                      href={mini.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="story-publisher-link"
                    >
                      Original link on {mini.source_id} ↗
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
