<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppNav from './components/AppNav.vue'
import FridgePalLoader from './components/FridgePalLoader.vue'
import { useRescueStore } from './features/rescue/rescueStore'
import { useInventoryStore } from './features/storage/inventoryStore'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const hideNavigation = computed(() => route.meta.hideNavigation === true)

const TAB_PATHS = ['/', '/rescue', '/recipes', '/history']
const transitionName = ref('route-fade')

router.beforeEach((to, from) => {
  const toTab = TAB_PATHS.includes(to.path)
  const fromTab = TAB_PATHS.includes(from.path)
  if (toTab && fromTab) {
    transitionName.value = 'route-fade'
  } else if (toTab && !fromTab) {
    transitionName.value = 'route-pop'
  } else {
    transitionName.value = 'route-push'
  }
})

const { inventory, hydrateFromServer } = useInventoryStore()
const { searching, searchResult, latestSessionId } = useRescueStore(inventory)

const showCompleteDialog = ref(false)
const initialHydrationPending = ref(true)
const showInitialLoader = ref(false)
let initialLoaderTimer: ReturnType<typeof setTimeout> | undefined

onMounted(() => {
  initialLoaderTimer = setTimeout(() => {
    showInitialLoader.value = true
  }, 150)

  void hydrateFromServer().finally(() => {
    if (initialLoaderTimer !== undefined) {
      clearTimeout(initialLoaderTimer)
      initialLoaderTimer = undefined
    }
    showInitialLoader.value = false
    initialHydrationPending.value = false
  })
})

onBeforeUnmount(() => {
  if (initialLoaderTimer !== undefined) {
    clearTimeout(initialLoaderTimer)
    initialLoaderTimer = undefined
  }
})

watch(() => searching.value, (now, was) => {
  if (was && !now && searchResult.value) {
    showCompleteDialog.value = true
  }
})

function goToMealIdea() {
  showCompleteDialog.value = false
  if (latestSessionId.value) {
    void router.push({ path: '/history', query: { tab: 'meal-ideas', mealIdeaNewId: latestSessionId.value } })
  }
}
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--task': hideNavigation }">
    <a href="#main-content" class="skip-link">{{ t('common.skipToContent') }}</a>
    <AppNav v-if="!hideNavigation" />
    <main id="main-content" class="app-content">
      <FridgePalLoader
        v-if="showInitialLoader"
        class="app-initial-loader"
        variant="page"
        :label="t('loading.initial')"
      />
      <router-view v-else-if="!initialHydrationPending" v-slot="{ Component }">
        <transition :name="transitionName" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <Teleport to="body">
      <Transition name="complete-dialog-fade">
        <div v-if="showCompleteDialog" class="complete-dialog-overlay" @click.self="showCompleteDialog = false">
          <div class="complete-dialog" role="alertdialog" aria-labelledby="complete-title">
            <h2 id="complete-title" class="complete-dialog__title">{{ t('mealIdeas.searchComplete') }}</h2>
            <p class="complete-dialog__desc">{{ t('mealIdeas.searchCompleteDesc') }}</p>
            <div class="complete-dialog__actions">
              <button class="complete-dialog__btn complete-dialog__btn--cancel" @click="showCompleteDialog = false">{{ t('common.cancel') }}</button>
              <button class="complete-dialog__btn complete-dialog__btn--confirm" @click="goToMealIdea">{{ t('mealIdeas.viewNow') }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.skip-link {
  position: absolute;
  z-index: 9999;
  top: -100px;
  left: 0;
  padding: var(--space-2) var(--space-4);
  border-radius: 0 0 var(--radius-md) 0;
  color: var(--color-on-primary);
  background: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.skip-link:focus {
  top: 0;
}

.app-shell {
  min-height: 100vh;
}

@media (min-width: 880px) {
  .app-shell {
    display: grid;
    grid-template-columns: 200px minmax(0, 1fr);
  }

  .app-shell--task {
    display: block;
  }
}
</style>

<style>
.complete-dialog-overlay {
  position: fixed;
  z-index: 9998;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgb(8 18 38 / 0.55);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.complete-dialog {
  width: min(90%, 360px);
  display: grid;
  gap: var(--space-4);
  padding: var(--space-6);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-overlay);
  text-align: center;
}

.complete-dialog__title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  line-height: var(--line-height-tight);
}

.complete-dialog__desc {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

.complete-dialog__actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-2);
}

.complete-dialog__btn {
  min-height: var(--tap-target-min);
  min-width: 120px;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  transition: background-color var(--duration-base) var(--ease-standard);
}

.complete-dialog__btn--cancel {
  background: var(--color-surface-sunken);
  color: var(--color-text);
}

.complete-dialog__btn--cancel:hover {
  background: var(--color-border);
}

.complete-dialog__btn--confirm {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.complete-dialog__btn--confirm:hover {
  opacity: 0.9;
}

.complete-dialog-fade-enter-active,
.complete-dialog-fade-leave-active {
  transition: opacity 0.2s var(--ease-standard);
}

.complete-dialog-fade-enter-from,
.complete-dialog-fade-leave-to {
  opacity: 0;
}
</style>
