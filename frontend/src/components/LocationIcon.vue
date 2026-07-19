<script setup lang="ts">
import type { StorageLocation } from '../features/storage/inventory'

withDefaults(defineProps<{ location: StorageLocation; size?: number }>(), { size: 18 })
</script>

<template>
  <svg
    class="location-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="location === 'fridge'">
      <rect x="6" y="2.5" width="12" height="19" rx="2.5" />
      <path d="M6 9.5h12M9 5.5v1.5M9 13v2.5" />
    </template>
    <template v-else-if="location === 'freezer'">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <path d="M12 7v10M7.7 9.5l8.6 5M16.3 9.5l-8.6 5" />
    </template>
    <template v-else>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <path d="M4 10h16M12 10v10M9 7h6M9.5 14.5h.01M14.5 14.5h.01" />
    </template>
  </svg>
</template>

<style scoped>
.location-icon {
  display: inline-block;
  flex: none;
  vertical-align: middle;
}
</style>
