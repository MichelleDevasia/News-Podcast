/**
 * TypeScript definitions for backend configuration options.
 * Matches schema returned by GET /api/options.
 */

export interface OptionItem {
  label: string;
  code: string;
}

export interface AccentItem {
  label: string;
  tld: string;
}

export interface OptionsResponse {
  categories: string[];
  countries: OptionItem[];
  languages: OptionItem[];
  accents: AccentItem[];
}
