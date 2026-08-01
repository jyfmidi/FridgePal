<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '../components/AppButton.vue'
import AppChip from '../components/AppChip.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { foodIcons } from '../components/food-token/icons'

/**
 * DEV-ONLY design token showcase (not linked from app navigation).
 * Screenshot review surface for the token scale, the Food Token icon
 * registry, and monogram fallbacks. Labels are English by design.
 */
const { t } = useI18n()

const keys = Object.keys(foodIcons)

const sampleSizes = [24, 32, 48, 64]
const sizeSampleKeys = ['chicken-breast', 'broccoli', 'lemon', 'frozen-peas']

const monogramSamples = ['Quinoa', '牛油果', 'Sourdough']

const urgencyScale = computed(() => [
  { level: 5, label: 'Past date', token: '--color-urgency-past', ink: '--color-urgency-past-ink' },
  { level: 4, label: 'Today', token: '--color-urgency-today', ink: '--color-urgency-today-ink' },
  { level: 3, label: '1–2 days', token: '--color-urgency-soon', ink: '--color-urgency-soon-ink' },
  { level: 2, label: '3–5 days', token: '--color-urgency-later', ink: '--color-urgency-later-ink' },
  { level: 1, label: 'Later', token: '--color-urgency-neutral', ink: '--color-urgency-neutral-ink' },
])
</script>

<template>
  <div class="dev-tokens">
    <header class="dev-tokens__header">
      <h1>Dev showcase · design tokens</h1>
      <p>Dev-only route (<code>/dev/tokens</code>), not part of app navigation. {{ t('app.title') }} design foundation review surface.</p>
    </header>

    <section class="dev-tokens__section">
      <h2>Urgency scale (UI-01)</h2>
      <div class="dev-tokens__swatches">
        <div
          v-for="u in urgencyScale"
          :key="u.level"
          class="dev-tokens__swatch"
          :style="{ backgroundColor: `var(${u.token})`, color: `var(${u.ink})` }"
        >
          <strong>{{ u.label }}</strong>
          <span>L{{ u.level }} · {{ u.token }}</span>
        </div>
      </div>
    </section>

    <section class="dev-tokens__section">
      <h2>Icon registry · light surface</h2>
      <div class="dev-tokens__grid dev-tokens__grid--light">
        <figure v-for="key in keys" :key="key" class="dev-tokens__cell">
          <FoodToken :food-key="key" :name="key" :size="48" />
          <figcaption>{{ key }}</figcaption>
        </figure>
      </div>
    </section>

    <section class="dev-tokens__section">
      <h2>Icon registry · neutral selection tray</h2>
      <div class="dev-tokens__grid dev-tokens__grid--tray">
        <figure v-for="key in keys" :key="key" class="dev-tokens__cell">
          <FoodToken :food-key="key" :name="key" :size="48" />
          <figcaption>{{ key }}</figcaption>
        </figure>
      </div>
    </section>

    <section class="dev-tokens__section">
      <h2>Size ramp</h2>
      <div class="dev-tokens__sizes">
        <div v-for="size in sampleSizes" :key="size" class="dev-tokens__size-row">
          <span class="dev-tokens__size-label">{{ size }}px</span>
          <FoodToken v-for="key in sizeSampleKeys" :key="key" :food-key="key" :name="key" :size="size" />
        </div>
      </div>
    </section>

    <section class="dev-tokens__section">
      <h2>Monogram fallbacks</h2>
      <div class="dev-tokens__sizes">
        <div class="dev-tokens__size-row">
          <FoodToken v-for="name in monogramSamples" :key="name" :name="name" :size="48" />
        </div>
        <div class="dev-tokens__size-row dev-tokens__size-row--tray">
          <FoodToken v-for="name in monogramSamples" :key="name" :name="name" :size="48" />
        </div>
        <p class="dev-tokens__note">{{ monogramSamples.join(' · ') }}</p>
      </div>
    </section>

    <section class="dev-tokens__section">
      <h2>Primitives</h2>
      <div class="dev-tokens__size-row">
        <AppButton variant="primary">Primary</AppButton>
        <AppButton variant="secondary">Secondary</AppButton>
        <AppButton variant="ghost">Ghost</AppButton>
        <AppButton disabled>Disabled</AppButton>
      </div>
      <div class="dev-tokens__size-row">
        <AppChip selected>All</AppChip>
        <AppChip>Fridge</AppChip>
        <AppChip>Freezer</AppChip>
        <AppChip disabled>Pantry</AppChip>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dev-tokens {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-4) var(--space-12);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.dev-tokens__header h1 {
  font-size: var(--font-size-xl);
}

.dev-tokens__header p {
  margin-top: var(--space-1);
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.dev-tokens__section h2 {
  font-size: var(--font-size-base);
  margin-bottom: var(--space-3);
}

.dev-tokens__swatches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--space-2);
}

.dev-tokens__swatch {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
}

.dev-tokens__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(76px, 1fr));
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-lg);
}

.dev-tokens__grid--light {
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.dev-tokens__grid--tray {
  background: var(--color-selection-tray);
  box-shadow: inset 0 0 0 1px var(--color-selection-edge);
}

.dev-tokens__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--color-muted);
}

.dev-tokens__sizes {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.dev-tokens__size-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.dev-tokens__size-row--tray {
  background: var(--color-selection-tray);
  box-shadow: inset 0 0 0 1px var(--color-selection-edge);
}

.dev-tokens__size-label {
  min-width: 40px;
  font-size: var(--font-size-xs);
  color: var(--color-muted);
}

.dev-tokens__note {
  font-size: var(--font-size-xs);
  color: var(--color-muted);
}
</style>
