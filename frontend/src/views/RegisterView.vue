<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../features/auth/authStore'

const router = useRouter()
const { register } = useAuth()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const submitting = ref(false)

async function handleSubmit() {
  error.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  submitting.value = true
  try {
    await register(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Registration failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <form class="auth-card" @submit.prevent="handleSubmit">
      <h1 class="auth-card__title">Fridge Pal</h1>
      <p class="auth-card__subtitle">Create your kitchen account</p>

      <div class="auth-field">
        <label for="reg-username" class="auth-field__label">Username</label>
        <input
          id="reg-username"
          v-model="username"
          type="text"
          class="auth-field__input"
          autocomplete="username"
          placeholder="3-32 chars, letters/numbers/_/-"
          required
        >
      </div>

      <div class="auth-field">
        <label for="reg-password" class="auth-field__label">Password</label>
        <input
          id="reg-password"
          v-model="password"
          type="password"
          class="auth-field__input"
          autocomplete="new-password"
          placeholder="At least 8 characters"
          required
        >
      </div>

      <div class="auth-field">
        <label for="reg-confirm" class="auth-field__label">Confirm password</label>
        <input
          id="reg-confirm"
          v-model="confirmPassword"
          type="password"
          class="auth-field__input"
          autocomplete="new-password"
          required
        >
      </div>

      <p v-if="error" class="auth-error" role="alert">{{ error }}</p>

      <button
        type="submit"
        class="auth-submit"
        :disabled="submitting"
      >
        {{ submitting ? 'Creating…' : 'Register' }}
      </button>

      <p class="auth-link">
        Already have an account?
        <router-link to="/login">Log in</router-link>
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

.auth-field__input::placeholder {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
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
