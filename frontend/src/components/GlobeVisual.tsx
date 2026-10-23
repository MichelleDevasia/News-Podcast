import React from 'react';
import './GlobeVisual.css';

interface GlobeVisualProps {
  theme: 'dark' | 'light';
}

export const GlobeVisual: React.FC<GlobeVisualProps> = ({ theme }) => {
  return (
    <div className={`globe-wrapper ${theme}`} aria-label="Animated global news visualization">
      {/* Surrounding News Category Indicators */}
      <div className="category-indicator cat-tech">
        <div className="cat-badge">
          <span className="cat-dot dot-tech"></span>
          <span className="cat-name">Technology</span>
        </div>
        <div className="cat-line line-tech"></div>
      </div>

      <div className="category-indicator cat-world">
        <div className="cat-badge">
          <span className="cat-dot dot-world"></span>
          <span className="cat-name">World</span>
        </div>
        <div className="cat-line line-world"></div>
      </div>

      <div className="category-indicator cat-business">
        <div className="cat-badge">
          <span className="cat-dot dot-biz"></span>
          <span className="cat-name">Business</span>
        </div>
        <div className="cat-line line-biz"></div>
      </div>

      <div className="category-indicator cat-health">
        <div className="cat-badge">
          <span className="cat-dot dot-health"></span>
          <span className="cat-name">Health</span>
        </div>
        <div className="cat-line line-health"></div>
      </div>

      {/* Main SVG Globe & Orbit System */}
      <svg
        className="globe-svg"
        viewBox="0 0 500 500"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
      >
        <defs>
          {/* Circular mask for sphere */}
          <clipPath id="globe-clip">
            <circle cx="250" cy="250" r="140" />
          </clipPath>

          {/* Spherical depth gradient */}
          <radialGradient id="sphere-lighting" cx="40%" cy="35%" r="75%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity={theme === 'dark' ? '0.15' : '0.4'} />
            <stop offset="50%" stopColor="#000000" stopOpacity="0" />
            <stop offset="100%" stopColor="#000000" stopOpacity={theme === 'dark' ? '0.65' : '0.35'} />
          </radialGradient>

          {/* Atmosphere rim gradient */}
          <radialGradient id="atmosphere-rim" cx="50%" cy="50%" r="50%">
            <stop offset="85%" stopColor={theme === 'dark' ? '#38bdf8' : '#0284c7'} stopOpacity="0" />
            <stop offset="100%" stopColor={theme === 'dark' ? '#38bdf8' : '#0284c7'} stopOpacity={theme === 'dark' ? '0.45' : '0.25'} />
          </radialGradient>

          {/* Glow filter */}
          <filter id="soft-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Path for Orbit 1 satellite motion */}
          <path
            id="orbit-path-1"
            d="M 60,250 A 200,75 -24 1,1 440,250 A 200,75 -24 1,1 60,250"
          />

          {/* Path for Orbit 2 satellite motion */}
          <path
            id="orbit-path-2"
            d="M 70,250 A 195,65 32 1,1 430,250 A 195,65 32 1,1 70,250"
          />
        </defs>

        {/* Ambient background glow ring */}
        <circle
          cx="250"
          cy="250"
          r="146"
          className="globe-glow-rim"
          fill="none"
          stroke={theme === 'dark' ? 'rgba(56, 189, 248, 0.25)' : 'rgba(2, 132, 199, 0.2)'}
          strokeWidth="1.5"
          filter="url(#soft-glow)"
        />

        {/* Outer orbital rings (rendered behind the globe) */}
        <g className="orbit-system-back">
          <ellipse
            cx="250"
            cy="250"
            rx="195"
            ry="75"
            transform="rotate(-24 250 250)"
            className="orbit-ring orbit-ring-1"
          />
          <ellipse
            cx="250"
            cy="250"
            rx="190"
            ry="65"
            transform="rotate(32 250 250)"
            className="orbit-ring orbit-ring-2"
          />
        </g>

        {/* Base Ocean Sphere */}
        <circle cx="250" cy="250" r="140" className="ocean-sphere" />

        {/* Rotating Continents Layer (Clipped to sphere) */}
        <g clipPath="url(#globe-clip)">
          <g className="continents-track">
            {/* World Map Tile 1 */}
            <g className="world-tile" transform="translate(0, 110)">
              {/* North America */}
              <path
                d="M 45,35 C 55,25 75,20 95,25 C 110,30 115,45 105,65 C 98,75 80,75 75,90 C 70,105 60,110 50,95 C 42,80 35,70 38,55 Z"
                className="continent-land"
              />
              {/* Greenland */}
              <path
                d="M 115,15 C 125,12 135,18 130,28 C 122,35 112,30 115,15 Z"
                className="continent-land"
              />
              {/* South America */}
              <path
                d="M 75,105 C 90,105 100,120 95,145 C 90,170 80,200 68,220 C 62,210 65,185 68,160 C 70,135 65,115 75,105 Z"
                className="continent-land"
              />
              {/* Europe */}
              <path
                d="M 145,35 C 160,30 175,32 178,48 C 170,55 160,58 152,65 C 145,60 140,48 145,35 Z"
                className="continent-land"
              />
              {/* Africa */}
              <path
                d="M 148,70 C 165,65 190,75 195,105 C 190,135 178,165 165,185 C 155,175 145,150 142,125 C 140,100 138,80 148,70 Z"
                className="continent-land"
              />
              {/* Asia */}
              <path
                d="M 180,30 C 215,22 265,30 280,55 C 290,75 285,95 270,110 C 255,105 240,95 230,115 C 220,135 210,130 205,105 C 200,85 185,75 180,50 Z"
                className="continent-land"
              />
              {/* India */}
              <path
                d="M 215,105 C 228,105 235,118 225,135 C 218,125 215,115 215,105 Z"
                className="continent-land"
              />
              {/* Australia */}
              <path
                d="M 260,160 C 285,155 295,175 290,195 C 275,205 255,198 252,180 Z"
                className="continent-land"
              />
            </g>

            {/* World Map Tile 2 (Seamless loop offset by 320px) */}
            <g className="world-tile" transform="translate(320, 110)">
              {/* North America */}
              <path
                d="M 45,35 C 55,25 75,20 95,25 C 110,30 115,45 105,65 C 98,75 80,75 75,90 C 70,105 60,110 50,95 C 42,80 35,70 38,55 Z"
                className="continent-land"
              />
              {/* Greenland */}
              <path
                d="M 115,15 C 125,12 135,18 130,28 C 122,35 112,30 115,15 Z"
                className="continent-land"
              />
              {/* South America */}
              <path
                d="M 75,105 C 90,105 100,120 95,145 C 90,170 80,200 68,220 C 62,210 65,185 68,160 C 70,135 65,115 75,105 Z"
                className="continent-land"
              />
              {/* Europe */}
              <path
                d="M 145,35 C 160,30 175,32 178,48 C 170,55 160,58 152,65 C 145,60 140,48 145,35 Z"
                className="continent-land"
              />
              {/* Africa */}
              <path
                d="M 148,70 C 165,65 190,75 195,105 C 190,135 178,165 165,185 C 155,175 145,150 142,125 C 140,100 138,80 148,70 Z"
                className="continent-land"
              />
              {/* Asia */}
              <path
                d="M 180,30 C 215,22 265,30 280,55 C 290,75 285,95 270,110 C 255,105 240,95 230,115 C 220,135 210,130 205,105 C 200,85 185,75 180,50 Z"
                className="continent-land"
              />
              {/* India */}
              <path
                d="M 215,105 C 228,105 235,118 225,135 C 218,125 215,115 215,105 Z"
                className="continent-land"
              />
              {/* Australia */}
              <path
                d="M 260,160 C 285,155 295,175 290,195 C 275,205 255,198 252,180 Z"
                className="continent-land"
              />
            </g>

            {/* World Map Tile 3 (Prevents edge gap during rotation) */}
            <g className="world-tile" transform="translate(640, 110)">
              <path
                d="M 45,35 C 55,25 75,20 95,25 C 110,30 115,45 105,65 C 98,75 80,75 75,90 C 70,105 60,110 50,95 Z"
                className="continent-land"
              />
              <path
                d="M 75,105 C 90,105 100,120 95,145 C 90,170 80,200 68,220 Z"
                className="continent-land"
              />
            </g>
          </g>

          {/* Longitudinal & Latitudinal Coordinate Grid Lines */}
          <g className="globe-grid">
            <ellipse cx="250" cy="250" rx="140" ry="40" className="grid-line" />
            <ellipse cx="250" cy="250" rx="140" ry="90" className="grid-line" />
            <ellipse cx="250" cy="250" rx="40" ry="140" className="grid-line" />
            <ellipse cx="250" cy="250" rx="90" ry="140" className="grid-line" />
            <line x1="110" y1="250" x2="390" y2="250" className="grid-line equator" />
            <line x1="250" y1="110" x2="250" y2="390" className="grid-line meridian" />
          </g>

          {/* Telemetry data beacon points on sphere */}
          <g className="beacon-points">
            <circle cx="210" cy="215" r="3.5" className="beacon beacon-1" />
            <circle cx="280" cy="235" r="3" className="beacon beacon-2" />
            <circle cx="240" cy="280" r="3" className="beacon beacon-3" />
          </g>

          {/* Spherical lighting & depth overlay */}
          <circle cx="250" cy="250" r="140" fill="url(#sphere-lighting)" />

          {/* Atmospheric edge glow */}
          <circle cx="250" cy="250" r="140" fill="url(#atmosphere-rim)" />
        </g>

        {/* Orbit Front Paths & Moving Telemetry Nodes */}
        <g className="orbit-system-front">
          {/* Orbital Satellite Node 1 */}
          <circle r="4" className="orbit-satellite sat-1">
            <animateMotion
              dur="14s"
              repeatCount="indefinite"
              rotate="auto"
            >
              <mpath href="#orbit-path-1" />
            </animateMotion>
          </circle>

          {/* Orbital Satellite Node 2 (Counter motion) */}
          <circle r="3.5" className="orbit-satellite sat-2">
            <animateMotion
              dur="18s"
              repeatCount="indefinite"
              rotate="auto"
              keyPoints="1;0"
              keyTimes="0;1"
            >
              <mpath href="#orbit-path-2" />
            </animateMotion>
          </circle>

          {/* Orbital Satellite Node 3 */}
          <circle r="2.5" className="orbit-satellite sat-3">
            <animateMotion
              dur="14s"
              begin="-7s"
              repeatCount="indefinite"
              rotate="auto"
            >
              <mpath href="#orbit-path-1" />
            </animateMotion>
          </circle>
        </g>
      </svg>
    </div>
  );
};
