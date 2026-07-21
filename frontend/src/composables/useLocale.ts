/**
 * Locale state shared across the app. Holds the active locale, syncs
 * vue-i18n and <html lang>, and persists the choice to localStorage.
 */
import { computed, type WritableComputedRef } from 'vue'
import { useI18n } from 'vue-i18n'

export const SUPPORTED_LOCALES = ['en', 'zh-CN'] as const
export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

const LOCALE_STORAGE_KEY = 'fridge-pal-locale'

/** stored preference -> browser language (zh* -> zh-CN, else en) -> 'en' */
export function detectInitialLocale(): AppLocale {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
  if (stored === 'en' || stored === 'zh-CN') return stored
  return navigator.language.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en'
}

/** Apply the detected/stored locale at app startup (before i18n is used). */
export function initLocale(locale: WritableComputedRef<string>) {
  locale.value = detectInitialLocale()
  document.documentElement.lang = locale.value
}

export function useLocale() {
  const { locale } = useI18n()
  const activeLocale = computed(() => locale.value as AppLocale)

  function setLocale(next: AppLocale) {
    locale.value = next
    document.documentElement.lang = next
    localStorage.setItem(LOCALE_STORAGE_KEY, next)
  }

  function toggleLocale() {
    setLocale(activeLocale.value === 'en' ? 'zh-CN' : 'en')
  }

  return { locale: activeLocale, setLocale, toggleLocale }
}
