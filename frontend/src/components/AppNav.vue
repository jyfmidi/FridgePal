<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const destinations = [
  { to: '/', label: 'navigation.storage', icon: 'storage' },
  { to: '/rescue', label: 'navigation.rescue', icon: 'rescue' },
  { to: '/recipes', label: 'navigation.recipes', icon: 'recipes' },
  { to: '/history', label: 'navigation.history', icon: 'history' },
] as const
</script>

<template>
  <nav class="app-nav" :aria-label="t('navigation.label')">
    <RouterLink v-for="item in destinations" :key="item.to" :to="item.to" class="app-nav__item">
      <span class="app-nav__icon" aria-hidden="true">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <!-- Storage: fridge -->
          <template v-if="item.icon === 'storage'">
            <rect x="5.5" y="2.5" width="13" height="19" rx="2.5" />
            <path d="M5.5 9.5h13" />
            <path d="M8.5 5.5v1.5" />
            <path d="M8.5 13v2.5" />
          </template>
          <!-- Rescue: life ring -->
          <template v-else-if="item.icon === 'rescue'">
            <circle cx="12" cy="12" r="8.5" />
            <circle cx="12" cy="12" r="3.5" />
            <path d="M6 6l3.5 3.5" />
            <path d="M18 6l-3.5 3.5" />
            <path d="M6 18l3.5-3.5" />
            <path d="M18 18l-3.5-3.5" />
          </template>
          <!-- Recipes: open book -->
          <template v-else-if="item.icon === 'recipes'">
            <path d="M12 6.5c-1.8-1.6-4.4-2-7.5-2v13c3.1 0 5.7.4 7.5 2 1.8-1.6 4.4-2 7.5-2v-13c-3.1 0-5.7.4-7.5 2Z" />
            <path d="M12 6.5v13" />
          </template>
          <!-- History: clock -->
          <template v-else>
            <circle cx="12" cy="12" r="8.5" />
            <path d="M12 7v5l3.5 2" />
          </template>
        </svg>
      </span>
      <span>{{ t(item.label) }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.app-nav {
  position: fixed;
  z-index: var(--z-nav);
  right: 0;
  bottom: 0;
  left: 0;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: var(--space-1) max(var(--space-2), var(--safe-area-right)) calc(var(--space-1) + var(--safe-area-bottom)) max(var(--space-2), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.app-nav__item {
  position: relative;
  display: flex;
  min-height: 54px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  font-size: 0.6875rem;
  font-weight: var(--font-weight-medium);
  transition:
    color var(--duration-base) var(--ease-standard),
    background-color var(--duration-base) var(--ease-standard);
}

/* Active indicator bar (mobile: top edge). Doubles as a non-color cue. */
.app-nav__item::before {
  content: '';
  position: absolute;
  top: 0;
  right: 50%;
  width: 24px;
  height: 2.5px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  transform: translateX(50%) scaleX(0);
  transform-origin: center;
  transition: transform var(--duration-base) var(--ease-pop);
}

.app-nav__item.router-link-active {
  color: var(--color-primary);
}

.app-nav__item.router-link-active::before {
  transform: translateX(50%) scaleX(1);
}

.app-nav__icon {
  display: grid;
  place-items: center;
}

.app-nav__icon svg {
  width: 22px;
  height: 22px;
}

.app-nav__item.router-link-active .app-nav__icon svg {
  stroke-width: 2.1;
}

@media (min-width: 880px) {
  .app-nav {
    position: sticky;
    top: 0;
    right: auto;
    bottom: auto;
    left: auto;
    width: 200px;
    height: 100vh;
    grid-template-columns: 1fr;
    align-content: start;
    gap: var(--space-2);
    padding: 88px var(--space-4) var(--space-4);
    border-top: 0;
    border-right: 1px solid var(--color-border);
  }

  .app-nav__item {
    min-height: 48px;
    flex-direction: row;
    justify-content: flex-start;
    gap: var(--space-3);
    padding: 0 var(--space-3);
    font-size: var(--font-size-sm);
  }

  /* Desktop: soft tinted background instead of the top bar. */
  .app-nav__item::before {
    inset: 0;
    width: auto;
    height: auto;
    border-radius: var(--radius-md);
    background: var(--color-primary-softer);
    opacity: 0;
    transform: none;
    transition: opacity var(--duration-base) var(--ease-standard);
  }

  .app-nav__item.router-link-active::before {
    opacity: 1;
    transform: none;
  }

  .app-nav__item > * {
    position: relative;
  }
}
</style>
