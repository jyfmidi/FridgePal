import { createRouter, createWebHistory } from 'vue-router'
import ComingSoonView from './views/ComingSoonView.vue'
import StorageView from './views/StorageView.vue'
import AddFoodView from './views/AddFoodView.vue'
import ChooseFoodsView from './views/ChooseFoodsView.vue'
import RescueView from './views/RescueView.vue'
import RecipeResultsView from './views/RecipeResultsView.vue'
import RecipeEditorView from './views/RecipeEditorView.vue'
import RecipesView from './views/RecipesView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'storage', component: StorageView },
    { path: '/rescue', name: 'rescue', component: RescueView },
    { path: '/rescue/choose', name: 'rescue-choose', component: ChooseFoodsView, meta: { hideNavigation: true } },
    { path: '/rescue/results', name: 'rescue-results', component: RecipeResultsView },
    { path: '/recipes/editor', name: 'recipe-editor', component: RecipeEditorView, meta: { hideNavigation: true } },
    { path: '/recipes', name: 'recipes', component: RecipesView },
    { path: '/history', name: 'history', component: ComingSoonView, props: { titleKey: 'navigation.history' } },
    { path: '/add-food', name: 'add-food', component: AddFoodView, meta: { hideNavigation: true } },
    { path: '/storage/item', name: 'storage-item', component: () => import('./views/StorageItemView.vue'), meta: { hideNavigation: true } },
    {
      // Dev-only design token showcase; intentionally not linked from app navigation.
      path: '/dev/tokens',
      name: 'dev-tokens',
      component: () => import('./views/DevTokens.vue'),
    },
  ],
})
