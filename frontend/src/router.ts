import { createRouter, createWebHistory } from 'vue-router'
import StorageView from './views/StorageView.vue'
import AddFoodView from './views/AddFoodView.vue'
import ChooseFoodsView from './views/ChooseFoodsView.vue'
import RescueView from './views/RescueView.vue'
import RecipeResultsView from './views/RecipeResultsView.vue'
import RecipeEditorView from './views/RecipeEditorView.vue'
import RecipeReadView from './views/RecipeReadView.vue'
import RecipesView from './views/RecipesView.vue'
import HistoryView from './views/HistoryView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import { useAuth } from './features/auth/authStore'

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 }
  },
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { hideNavigation: true, public: true } },
    { path: '/register', name: 'register', component: RegisterView, meta: { hideNavigation: true, public: true } },
    { path: '/', name: 'storage', component: StorageView },
    { path: '/rescue', name: 'rescue', component: RescueView },
    { path: '/rescue/choose', name: 'rescue-choose', component: ChooseFoodsView, meta: { hideNavigation: true } },
    { path: '/rescue/results', name: 'rescue-results', component: RecipeResultsView },
    { path: '/recipes/editor', name: 'recipe-editor', component: RecipeEditorView, meta: { hideNavigation: true } },
    { path: '/recipes/view', name: 'recipe-read', component: RecipeReadView, meta: { hideNavigation: true } },
    { path: '/recipes', name: 'recipes', component: RecipesView },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/history/meal-idea/:sessionId', name: 'meal-idea-detail', component: () => import('./views/MealIdeaDetailView.vue') },
    { path: '/admin', name: 'admin', component: () => import('./views/AdminView.vue'), meta: { adminOnly: true } },
    { path: '/admin/foods/new', name: 'admin-food-new', component: () => import('./views/AdminFoodEditView.vue'), meta: { adminOnly: true, hideNavigation: true } },
    { path: '/admin/foods/:foodKey', name: 'admin-food-edit', component: () => import('./views/AdminFoodEditView.vue'), meta: { adminOnly: true, hideNavigation: true } },
    { path: '/add-food', name: 'add-food', component: AddFoodView, meta: { hideNavigation: true } },
    { path: '/storage/item', name: 'storage-item', component: () => import('./views/StorageItemView.vue'), meta: { hideNavigation: true } },
    {
      // Dev-only design token showcase; intentionally not linked from app navigation.
      path: '/dev/tokens',
      name: 'dev-tokens',
      component: () => import('./views/DevTokens.vue'),
      meta: { public: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const { isAuthenticated, init } = useAuth()
  if (!isAuthenticated.value) {
    try {
      await init()
    } catch {
      // Server unreachable: fall through so the guard can still route to
      // /login instead of leaving the navigation stuck.
    }
  }
  if (isAuthenticated.value && (to.name === 'login' || to.name === 'register')) {
    return { name: 'storage' }
  }
  if (!isAuthenticated.value && !to.meta.public) {
    return { name: 'login' }
  }
  if (to.meta.adminOnly && !useAuth().isAdmin.value) {
    return { name: 'storage' }
  }
})
