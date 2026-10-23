import React from 'react';
import './CategoryNav.css';

interface CategoryNavProps {
  categories: string[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  onOpenBriefingStudio: () => void;
}

export const CategoryNav: React.FC<CategoryNavProps> = ({
  categories: _categories,
  selectedCategory,
  onSelectCategory,
  onOpenBriefingStudio,
}) => {
  // Editorial curated subset of categories to display in the main header ribbon
  // (All 24 categories remain accessible in the Briefing Studio dropdown)
  const defaultDisplayCategories = [
    'General',
    'World',
    'Politics',
    'Technology',
    'Business',
    'Science',
    'Health',
    'Environment',
    'Sports',
  ];

  // Map display labels to backend category keys
  const categoryKeyMap: Record<string, string> = {
    'General': 'General',
    'World': 'International & World News',
    'Politics': 'Politics & Governance',
    'Technology': 'Technology & Software',
    'Business': 'Business & Corporate',
    'Science': 'Science & Space Exploration',
    'Health': 'Health & Medicine',
    'Environment': 'Environment & Climate Change',
    'Sports': 'Sports & Athletics',
  };

  const isCurrentActive = (displayLabel: string) => {
    const backendKey = categoryKeyMap[displayLabel] || displayLabel;
    return selectedCategory === backendKey || (displayLabel === 'General' && selectedCategory === 'General');
  };

  return (
    <nav className="catnav-container" aria-label="Editorial News Sections">
      <div className="catnav-content">
        <ul className="catnav-list">
          {defaultDisplayCategories.map((catLabel) => {
            const backendKey = categoryKeyMap[catLabel] || catLabel;
            const active = isCurrentActive(catLabel);
            return (
              <li key={catLabel} className="catnav-item">
                <button
                  type="button"
                  className={`catnav-btn ${active ? 'active' : ''}`}
                  onClick={() => onSelectCategory(backendKey)}
                  aria-current={active ? 'page' : undefined}
                >
                  {catLabel}
                </button>
              </li>
            );
          })}
        </ul>

        {/* Quick studio launcher in the navigation ribbon */}
        <div className="catnav-action">
          <button
            type="button"
            className="catnav-studio-btn"
            onClick={onOpenBriefingStudio}
            title="Open Briefing Studio to customize destination, topic, and voice"
          >
            <span className="studio-icon">⚙️</span>
            <span>Studio</span>
          </button>
        </div>
      </div>
    </nav>
  );
};
