<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from './components/AppNav.vue'

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
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--task': hideNavigation }">
    <a href="#main-content" class="skip-link">{{ $t('common.skipToContent') }}</a>
    <AppNav v-if="!hideNavigation" />
    <main id="main-content" class="app-content">
      <router-view v-slot="{ Component }">
        <transition :name="transitionName" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

@media (min-width: 880px) {
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
    display: grid;
    grid-template-columns: 200px minmax(0, 1fr);
  }

  .app-shell--task {
    display: block;
  }
}
</style>
