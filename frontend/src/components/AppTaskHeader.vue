<script setup lang="ts">
defineProps<{ title: string; backLabel: string; status?: string }>()
defineEmits<{ back: [] }>()
</script>

<template>
  <header class="app-task-header">
    <button class="app-task-header__back" type="button" :aria-label="backLabel" @click="$emit('back')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="m15 18-6-6 6-6" />
      </svg>
    </button>
    <h1>{{ title }}</h1>
    <div class="app-task-header__action">
      <slot name="action">
        <span v-if="status">{{ status }}</span>
      </slot>
    </div>
  </header>
</template>

<style scoped>
.app-task-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: minmax(64px, 1fr) auto minmax(64px, 1fr);
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}

.app-task-header__back {
  display: grid;
  width: var(--tap-target-min);
  min-height: var(--tap-target-min);
  place-items: center;
  justify-self: start;
  border-radius: var(--radius-sm);
  color: var(--color-primary);
}

.app-task-header__back svg {
  width: 24px;
  height: 24px;
}

.app-task-header h1 {
  max-width: min(55vw, 420px);
  overflow: hidden;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-task-header__action {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: flex-end;
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.app-task-header__action > span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-task-header__action :deep(button) {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

@media (min-width: 720px) {
  .app-task-header h1 {
    font-size: var(--font-size-lg);
  }
}
</style>
