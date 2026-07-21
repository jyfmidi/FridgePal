<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../features/auth/authStore'

const router = useRouter()
const { login } = useAuth()

const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    await login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Login failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <form class="auth-card" @submit.prevent="handleSubmit">
      <h1 class="auth-card__title">Fridge Pal</h1>
      <p class="auth-card__subtitle">Log in to your kitchen</p>

      <div class="auth-field">
        <label for="login-username" class="auth-field__label">Username</label>
        <input
          id="login-username"
          v-model="username"
          type="text"
          class="auth-field__input"
          autocomplete="username"
          required
        >
      </div>

      <div class="auth-field">
        <label for="login-password" class="auth-field__label">Password</label>
        <input
          id="login-password"
          v-model="password"
          type="password"
          class="auth-field__input"
          autocomplete="current-password"
          required
        >
      </div>

      <p v-if="error" class="auth-error" role="alert">{{ error }}</p>

      <button
        type="submit"
        class="auth-submit"
        :disabled="submitting"
      >
        {{ submitting ? 'Logging in…' : 'Log in' }}
      </button>

      <p class="auth-link">
        No account?
        <router-link to="/register">Register</router-link>
      </p>
    </form>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--space-6);
  background: var(--color-canvas);
}

.auth-card {
  width: min(90%, 380px);
  display: grid;
  gap: var(--space-4);
  padding: var(--space-8);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
}

.auth-card__title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: var(--letter-spacing-display);
  color: var(--color-brand);
  text-align: center;
}

.auth-card__subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-muted);
  text-align: center;
  margin-top: calc(var(--space-2) * -1);
}

.auth-field {
  display: grid;
  gap: var(--space-1);
}

.auth-field__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-ink-soft);
}

.auth-field__input {
  min-height: var(--tap-target-min);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-family: inherit;
  color: var(--color-ink);
  background: var(--color-surface);
  transition: border-color var(--duration-base) var(--ease-standard);
}

.auth-field__input:focus {
  outline: none;
  border-color: var(--color-focus-ring);
  box-shadow: 0 0 0 var(--focus-ring-width) var(--color-primary-softer);
}

.auth-error {
  font-size: var(--font-size-sm);
  color: var(--color-danger);
  background: var(--color-danger-soft);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
}

.auth-submit {
  min-height: var(--tap-target-min);
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-on-primary);
  background: var(--color-primary);
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-standard);
}

.auth-submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-link {
  font-size: var(--font-size-sm);
  color: var(--color-muted);
  text-align: center;
}

.auth-link a {
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
}

.auth-link a:hover {
  text-decoration: underline;
}
</style>
