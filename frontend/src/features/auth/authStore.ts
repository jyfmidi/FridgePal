import { computed, ref, watch } from 'vue'
import {
  fetchCurrentUser,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
} from '../../api/auth'
import type { AuthUser } from '../../api/auth'
import { resetFoodLibrary } from '../storage/libraryStore'

const currentUser = ref<AuthUser | null>(null)
/** Shared in-flight init so concurrent callers (router guard, App mount) await the same fetch. */
let initPromise: Promise<void> | null = null

// Authentication can also be cleared by the shared 401 handler in App.vue,
// so reset by observed identity rather than duplicating calls at each setter.
watch(
  () => currentUser.value?.username ?? null,
  () => resetFoodLibrary(),
)

export function useAuth() {
  const isAuthenticated = computed(() => currentUser.value !== null)
  const isAdmin = computed(() => currentUser.value?.isAdmin === true)

  function init(): Promise<void> {
    if (!initPromise) {
      initPromise = fetchCurrentUser()
        .then((user) => {
          currentUser.value = user
        })
        .finally(() => {
          initPromise = null
        })
    }
    return initPromise
  }

  async function login(username: string, password: string) {
    currentUser.value = await apiLogin(username, password)
  }

  async function register(username: string, password: string) {
    currentUser.value = await apiRegister(username, password)
  }

  async function logout() {
    // Best-effort server logout; local state always clears so the UI never
    // wedges on a failed request.
    try {
      await apiLogout()
    } catch {
      // Offline logout still ends the local session.
    } finally {
      currentUser.value = null
    }
  }

  return { currentUser, isAuthenticated, isAdmin, init, login, register, logout }
}
