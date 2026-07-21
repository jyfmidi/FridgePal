<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppButton from '../components/AppButton.vue'
import AppInput from '../components/AppInput.vue'
import AuthLayout from '../components/AuthLayout.vue'
import { useLocale } from '../composables/useLocale'
import { useAuth } from '../features/auth/authStore'

const router = useRouter()
const { t } = useI18n()
const { login } = useAuth()
const { toggleLocale } = useLocale()

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
    error.value = e instanceof Error ? e.message : t('auth.loginFailed')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout :tagline="t('auth.tagline')">
    <form class="auth-form" @submit.prevent="handleSubmit">
      <h2 class="auth-form__title">{{ t('auth.loginTitle') }}</h2>

      <AppInput
        id="login-username"
        v-model="username"
        :label="t('auth.username')"
        autocomplete="username"
        required
      />

      <AppInput
        id="login-password"
        v-model="password"
        :label="t('auth.password')"
        type="password"
        autocomplete="current-password"
        required
      />

      <p v-if="error" class="auth-form__error" role="alert">{{ error }}</p>

      <AppButton type="submit" block :disabled="submitting">
        {{ submitting ? t('auth.loggingIn') : t('auth.login') }}
      </AppButton>

      <p class="auth-form__link">
        {{ t('auth.noAccount') }}
        <router-link to="/register">{{ t('auth.register') }}</router-link>
      </p>
    </form>
    <template #footer>
      <button type="button" class="auth-locale-toggle" @click="toggleLocale">
        {{ t('auth.switchLocale') }}
      </button>
    </template>
  </AuthLayout>
</template>

<style scoped>
.auth-form {
  display: grid;
  gap: var(--space-4);
}

.auth-form__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: var(--letter-spacing-display);
  color: var(--color-ink);
  text-align: center;
}

.auth-form__error {
  font-size: var(--font-size-sm);
  color: var(--color-danger);
  background: var(--color-danger-soft);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
}

.auth-form__link {
  font-size: var(--font-size-sm);
  color: var(--color-muted);
  text-align: center;
}

.auth-form__link a {
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
}

.auth-form__link a:hover {
  text-decoration: underline;
}

.auth-locale-toggle {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-muted);
  border-radius: var(--radius-sm);
}

.auth-locale-toggle:hover {
  color: var(--color-ink-soft);
}
</style>
