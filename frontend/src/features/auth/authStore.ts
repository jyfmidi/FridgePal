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

export function useAuth() {
  const isAuthenticated = computed(() => currentUser.value !== null)

  async function init() {
    loading.value = true
    try {
      currentUser.value = await fetchCurrentUser()
    } finally {
      loading.value = false
    }
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
