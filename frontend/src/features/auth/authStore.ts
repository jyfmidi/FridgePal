import { ref, computed } from 'vue'
import {
  fetchCurrentUser,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
} from '../../api/auth'
import type { AuthUser } from '../../api/auth'

const currentUser = ref<AuthUser | null>(null)
const loading = ref(false)
/** Shared in-flight init so concurrent callers (router guard, App mount) await the same fetch. */
let initPromise: Promise<void> | null = null

export function useAuth() {
  const isAuthenticated = computed(() => currentUser.value !== null)

  function init(): Promise<void> {
    if (!initPromise) {
      loading.value = true
      initPromise = fetchCurrentUser()
        .then((user) => {
          currentUser.value = user
        })
        .finally(() => {
          loading.value = false
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
    await apiLogout()
    currentUser.value = null
  }

  return { currentUser, isAuthenticated, loading, init, login, register, logout }
}
