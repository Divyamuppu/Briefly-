import React, { useEffect, useState } from 'react';
import { Sun, Moon } from 'lucide-react';

const THEME_KEY = 'briefly-theme';

export const useTheme = () => {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light';
    return localStorage.getItem(THEME_KEY) || 'light';
  });

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return [theme, setTheme];
};

const ThemeToggle = ({ theme, setTheme }) => {
  const toggle = () => setTheme(theme === 'dark' ? 'light' : 'dark');

  return (
    <button
      type="button"
      data-testid="theme-toggle"
      onClick={toggle}
      aria-label="Toggle light/dark theme"
      className="inline-flex items-center justify-center w-9 h-9 rounded-full border border-border bg-secondary/50 hover:bg-secondary transition-colors"
    >
      {theme === 'dark' ? (
        <Sun className="w-4 h-4 text-primary" />
      ) : (
        <Moon className="w-4 h-4 text-primary" />
      )}
    </button>
  );
};

export default ThemeToggle;