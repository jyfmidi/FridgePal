<script setup lang="ts">
/**
 * Canonical form field: label + input + error message. First adopted by the
 * auth screens; designed to be reused by AddFood / StorageItem /
 * RecipeEditor later.
 */
import { computed, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    label: string
    type?: string
    placeholder?: string
    autocomplete?: string
    disabled?: boolean
    required?: boolean
    /** Error message shown below the input; also marks the field invalid. */
    error?: string
    /** Override the generated input id (useful for stable test selectors). */
    id?: string
  }>(),
  { type: 'text', placeholder: '', autocomplete: undefined, disabled: false, required: false, error: '', id: undefined },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const inputId = computed(() => props.id ?? `app-input-${useId()}`)
const errorId = computed(() => `${inputId.value}-error`)

function onInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="app-input" :class="{ 'app-input--error': error }">
    <label class="app-input__label" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      class="app-input__field"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :disabled="disabled"
      :required="required"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? errorId : undefined"
      @input="onInput"
    >
    <p v-if="error" :id="errorId" class="app-input__error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.app-input {
  display: grid;
  gap: var(--space-1);
}

.app-input__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-ink-soft);
}

.app-input__field {
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

.app-input__field::placeholder {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.app-input__field:focus {
  outline: none;
  border-color: var(--color-focus-ring);
  box-shadow: 0 0 0 var(--focus-ring-width) var(--color-primary-softer);
}

.app-input__field:disabled {
  color: var(--color-muted);
  background: var(--color-surface-sunken);
  cursor: not-allowed;
}

.app-input--error .app-input__field {
  border-color: var(--color-danger);
}

.app-input--error .app-input__field:focus {
  box-shadow: 0 0 0 var(--focus-ring-width) var(--color-danger-soft);
}

.app-input__error {
  font-size: var(--font-size-xs);
  color: var(--color-danger-ink);
}
</style>
