<script setup lang="ts">
export type AppIconName =
  | 'add'
  | 'calendar'
  | 'calendar-check'
  | 'chef'
  | 'edit'
  | 'globe'
  | 'grid'
  | 'ingredients'
  | 'instructions'
  | 'clock'
  | 'consume'
  | 'cooking-pot'
  | 'portions'
  | 'remove'
  | 'save'
  | 'search'
  | 'storage'
  | 'stock-in'
  | 'swap'
  | 'tombstone'
  | 'trash'
  | 'undo'
  | 'unit'
  | 'move'

withDefaults(defineProps<{ name: AppIconName; size?: number }>(), { size: 20 })
</script>

<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.9"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'add'">
      <path d="M12 5v14M5 12h14" />
    </template>
    <template v-else-if="name === 'remove'">
      <path d="M5 12h14" />
    </template>
    <template v-else-if="name === 'unit'">
      <path d="M4 7h16v10H4zM8 7v4M12 7v2M16 7v4" />
    </template>
    <template v-else-if="name === 'calendar' || name === 'calendar-check'">
      <rect x="3.5" y="5" width="17" height="15" rx="2.5" />
      <path d="M8 3v4M16 3v4M3.5 10h17" />
      <path v-if="name === 'calendar-check'" d="m8 15 2.2 2.2L16 12.5" />
    </template>
    <template v-else-if="name === 'portions'">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 4v8l5.7 5.7" />
    </template>
    <template v-else-if="name === 'ingredients'">
      <path d="M7 20c-2.5-4-1.2-8.3 2.7-10.2C13.7 7.8 16 5.6 17 3c2.4 5.6 1.4 12.5-4.4 15.6C10.8 19.6 8.9 20 7 20Z" />
      <path d="M7 20c1.6-4.2 4.2-7.6 8-10" />
    </template>
    <template v-else-if="name === 'instructions'">
      <path d="M9 6h11M9 12h11M9 18h11" />
      <circle cx="4.5" cy="6" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="18" r="1" />
    </template>
    <template v-else-if="name === 'edit'">
      <path d="M4 20h4l10.8-10.8a2.1 2.1 0 0 0-4-3L4 17z" />
      <path d="m13.5 7.5 3 3" />
    </template>
    <template v-else-if="name === 'globe'">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M3.5 12h17M12 3.5c2.2 2.3 3.3 5.1 3.3 8.5S14.2 18.2 12 20.5M12 3.5C9.8 5.8 8.7 8.6 8.7 12s1.1 6.2 3.3 8.5" />
    </template>
    <template v-else-if="name === 'grid'">
      <rect x="4" y="4" width="6" height="6" rx="1" />
      <rect x="14" y="4" width="6" height="6" rx="1" />
      <rect x="4" y="14" width="6" height="6" rx="1" />
      <rect x="14" y="14" width="6" height="6" rx="1" />
    </template>
    <template v-else-if="name === 'clock'">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7v5l3.5 2" />
    </template>
    <template v-else-if="name === 'search'">
      <circle cx="10.5" cy="10.5" r="5.5" />
      <path d="m15 15 4 4" />
    </template>
    <template v-else-if="name === 'swap'">
      <path d="M5 8h12M14 5l3 3-3 3M19 16H7M10 13l-3 3 3 3" />
    </template>
    <template v-else-if="name === 'tombstone'">
      <path d="M7 20v-9a5 5 0 0 1 10 0v9M4 20h16" />
      <path d="M12 9v7M9.5 11.5h5" />
    </template>
    <template v-else-if="name === 'save'">
      <path d="M5 3.5h11l3 3V20H5z" />
      <path d="M8 3.5V9h8V3.5M8 20v-7h8v7" />
    </template>
    <template v-else-if="name === 'storage'">
      <rect x="4" y="3" width="16" height="18" rx="3" />
      <path d="M4 10h16M8 6.5h.01M8 14v3" />
    </template>
    <template v-else-if="name === 'stock-in'">
      <path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4" />
      <path d="M8 14h8M12 3v8M8.5 7.5 12 11l3.5-3.5" />
      <path d="M18 3v4M16 5h4" />
    </template>
    <template v-else-if="name === 'consume'">
      <path d="M7 3v7M4.5 3v4.5A2.5 2.5 0 0 0 7 10a2.5 2.5 0 0 0 2.5-2.5V3M7 10v11" />
      <path d="M16.5 3c-2 2-2.5 4.7-2.5 7h4.5M17 3v18" />
    </template>
    <template v-else-if="name === 'move'">
      <rect x="3" y="7" width="6" height="10" rx="1.5" />
      <rect x="15" y="7" width="6" height="10" rx="1.5" />
      <path d="M9 12h6M12.5 9.5 15 12l-2.5 2.5" />
    </template>
    <template v-else-if="name === 'cooking-pot'">
      <path d="M5 10h14v7a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3z" />
      <path d="M3 10h18M7 8h10M2 13h3M19 13h3" />
      <path d="M9 6c-1-1 1-2 0-3M15 6c-1-1 1-2 0-3" />
    </template>
    <template v-else-if="name === 'chef'">
      <path d="M6 13c0 4 2.7 6 6 6s6-2 6-6" />
      <path d="M8 13V8a4 4 0 0 1 8 0v5" />
      <path d="M5 8a3 3 0 0 1 3-3 3 3 0 0 1 3 3" />
      <path d="M13 8a3 3 0 0 1 3-3 3 3 0 0 1 3 3" />
      <path d="M9 18v3M15 18v3" />
    </template>
    <template v-else-if="name === 'trash'">
      <path d="M5 7v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7" />
      <path d="M3 7h18" />
      <path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3" />
      <path d="M10 11v6M14 11v6" />
    </template>
    <template v-else-if="name === 'undo'">
      <path d="M9 7 4 12l5 5" />
      <path d="M5 12h8a6 6 0 0 1 6 6v1" />
    </template>
  </svg>
</template>

<style scoped>
.app-icon {
  display: inline-block;
  flex: none;
  vertical-align: middle;
}
</style>
