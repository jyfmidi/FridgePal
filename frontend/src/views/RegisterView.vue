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
const { register } = useAuth()
const { toggleLocale } = useLocale()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const submitting = ref(false)

const USERNAME_PATTERN = /^[a-zA-Z0-9_-]{3,32}$/

async function handleSubmit() {
  error.value = ''

  if (!USERNAME_PATTERN.test(username.value)) {
    error.value = t('auth.usernameInvalid')
    return
  }
  if (password.value.length < 8) {
    error.value = t('auth.passwordTooShort')
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = t('auth.passwordMismatch')
    return
  }

  submitting.value = true
  try {
    await register(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : t('auth.registerFailed')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout :tagline="t('auth.tagline')">
    <form class="auth-form" @submit.prevent="handleSubmit">
      <h2 class="auth-form__title">{{ t('auth.registerTitle') }}</h2>

      <AppInput
        id="reg-username"
        v-model="username"
        :label="t('auth.username')"
        :placeholder="t('auth.usernamePlaceholder')"
        autocomplete="username"
        required
      />

      <AppInput
        id="reg-password"
        v-model="password"
        :label="t('auth.password')"
        type="password"
        :placeholder="t('auth.passwordPlaceholder')"
        autocomplete="new-password"
        required
      />

      <AppInput
        id="reg-confirm"
        v-model="confirmPassword"
        :label="t('auth.confirmPassword')"
        type="password"
        autocomplete="new-password"
        required
      />

      <p v-if="error" class="auth-form__error" role="alert">{{ error }}</p>

      <AppButton type="submit" block :disabled="submitting">
        {{ submitting ? t('auth.registering') : t('auth.register') }}
      </AppButton>

      <p class="auth-form__link">
        {{ t('auth.haveAccount') }}
        <router-link to="/login">{{ t('auth.login') }}</router-link>
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
