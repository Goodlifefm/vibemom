import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

/**
 * Инициализация Telegram WebApp
 * - Применяем themeParams как CSS-переменные
 * - Вызываем ready() и expand()
 */
function initTelegramWebApp() {
  const tg = (window as { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp;

  if (!tg) {
    console.log('[TG] Telegram WebApp недоступен, запуск в браузере');
    return;
  }

  // Сообщаем Telegram что приложение готово
  tg.ready();

  // Раскрываем на весь экран
  if (tg.expand) {
    tg.expand();
  }

  // Применяем цветовую тему из Telegram
  applyThemeParams(tg.themeParams);

  // Слушаем изменения темы
  tg.onEvent?.('themeChanged', () => {
    applyThemeParams(tg.themeParams);
  });

  console.log('[TG] WebApp инициализирован:', {
    version: tg.version,
    platform: tg.platform,
    colorScheme: tg.colorScheme,
  });
}

/**
 * Применяем themeParams как CSS-переменные
 */
function applyThemeParams(params?: TelegramThemeParams) {
  if (!params) return;

  const root = document.documentElement;

  // Маппинг Telegram themeParams → CSS-переменные
  const mapping: Record<string, string> = {
    bg_color: '--bg-color',
    text_color: '--text-color',
    hint_color: '--text-muted',
    link_color: '--accent-color',
    button_color: '--accent-color',
    button_text_color: '--btn-text-color',
    secondary_bg_color: '--card-bg',
  };

  for (const [tgKey, cssVar] of Object.entries(mapping)) {
    const value = params[tgKey as keyof TelegramThemeParams];
    if (value) {
      root.style.setProperty(cssVar, value);
    }
  }
}

// Типы для Telegram WebApp
interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

interface TelegramWebApp {
  ready: () => void;
  expand?: () => void;
  close?: () => void;
  version?: string;
  platform?: string;
  colorScheme?: 'light' | 'dark';
  themeParams?: TelegramThemeParams;
  initData?: string;
  initDataUnsafe?: { user?: { id: number; username?: string } };
  onEvent?: (event: string, callback: () => void) => void;
}

// Инициализируем Telegram до рендера React
initTelegramWebApp();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
