import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  
  // Apply theme colors as CSS variables
  const theme = tg.themeParams;
  const root = document.documentElement;
  
  if (theme.bg_color) root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
  if (theme.text_color) root.style.setProperty('--tg-theme-text-color', theme.text_color);
  if (theme.hint_color) root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
  if (theme.link_color) root.style.setProperty('--tg-theme-link-color', theme.link_color);
  if (theme.button_color) root.style.setProperty('--tg-theme-button-color', theme.button_color);
  if (theme.button_text_color) root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
  if (theme.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
  if (theme.header_bg_color) root.style.setProperty('--tg-theme-header-bg-color', theme.header_bg_color);
  if (theme.accent_text_color) root.style.setProperty('--tg-theme-accent-text-color', theme.accent_text_color);
  if (theme.section_bg_color) root.style.setProperty('--tg-theme-section-bg-color', theme.section_bg_color);
  if (theme.section_header_text_color) root.style.setProperty('--tg-theme-section-header-text-color', theme.section_header_text_color);
  if (theme.subtitle_text_color) root.style.setProperty('--tg-theme-subtitle-text-color', theme.subtitle_text_color);
  if (theme.destructive_text_color) root.style.setProperty('--tg-theme-destructive-text-color', theme.destructive_text_color);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
