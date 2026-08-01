<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { foodIcons } from '../components/food-token/icons'
import { createFoodDefinition, deleteFoodDefinition, listFoodDefinitions, removeFoodIcon, updateFoodDefinition, uploadFoodIcon, type FoodDefinitionPayload } from '../api/admin'
import { registerCustomIcon } from '../components/food-token'
import type { LibraryFood } from '../api/library'
import { inventoryUnits, type InventoryUnit } from '../features/storage/inventory'
import { useFoodLibrary } from '../features/storage/libraryStore'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { hydrateLibrary } = useFoodLibrary()

const foodKey = computed(() => (route.params.foodKey as string | undefined) ?? '')
const isEditing = computed(() => foodKey.value.length > 0)
const title = computed(() => t(isEditing.value ? 'admin.editor.editTitle' : 'admin.editor.newTitle'))

const nameEn = ref('')
const nameZh = ref('')
const aliasesEn = ref('')
const aliasesZh = ref('')
const category = ref('other')
const visualKey = ref('')
const baseUnit = ref<InventoryUnit>('g')
const recommendedStorage = ref<'FRIDGE' | 'FREEZER' | 'PANTRY'>('FRIDGE')
const active = ref(true)
const shelfLifeDays = ref<Record<'FRIDGE' | 'FREEZER' | 'PANTRY', string>>({
  FRIDGE: '',
  FREEZER: '',
  PANTRY: '',
})
const presets = ref<{ labelEn: string; labelZh: string; amount: number; unit: InventoryUnit }[]>([])

const loading = ref(isEditing.value)
const saving = ref(false)
const error = ref('')
const notFound = ref(false)
const customIcon = ref<string | null>(null)
const iconUploading = ref(false)
const iconError = ref('')
const iconInput = ref<HTMLInputElement | null>(null)

const categorySuggestions = ['vegetable', 'fruit', 'dairy', 'protein', 'grain', 'seasoning', 'frozen', 'other']
const iconKeys = Object.keys(foodIcons).sort()

onMounted(async () => {
  if (!isEditing.value) return
  try {
    const foods = await listFoodDefinitions()
    const food = foods.find((item) => item.foodKey === foodKey.value)
    if (!food) {
      notFound.value = true
      return
    }
    applyFood(food)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : t('admin.errors.generic')
  } finally {
    loading.value = false
  }
})

function applyFood(food: LibraryFood) {
  nameEn.value = food.names.en
  nameZh.value = food.names['zh-CN'] ?? ''
  aliasesEn.value = (food.aliases.en ?? []).join(', ')
  aliasesZh.value = (food.aliases['zh-CN'] ?? []).join(', ')
  category.value = food.category
  visualKey.value = food.visualKey === food.foodKey ? '' : food.visualKey
  customIcon.value = food.customIcon
  if (food.customIcon) {
    registerCustomIcon(food.foodKey, food.customIcon)
  }
  baseUnit.value = food.baseUnit
  recommendedStorage.value = food.recommendedStorage
  active.value = food.active
  for (const rule of food.shelfLife) {
    shelfLifeDays.value[rule.storageLocation] = String(rule.durationDays)
  }
  presets.value = food.packagePresets.map((preset) => ({
    labelEn: preset.label.en,
    labelZh: preset.label['zh-CN'] ?? '',
    amount: Number(preset.amount),
    unit: preset.unit as InventoryUnit,
  }))
}

function splitAliases(raw: string): string[] {
  return raw
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
}

function addPreset() {
  presets.value.push({ labelEn: '', labelZh: '', amount: 1, unit: baseUnit.value })
}

function removePreset(index: number) {
  presets.value.splice(index, 1)
}

function buildPayload(): FoodDefinitionPayload {
  const shelfLife = (['FRIDGE', 'FREEZER', 'PANTRY'] as const)
    .filter((location) => shelfLifeDays.value[location] !== '')
    .map((location) => ({
      storageLocation: location,
      durationDays: Number(shelfLifeDays.value[location]),
    }))
  return {
    foodKey: undefined,
    names: {
      en: nameEn.value.trim(),
      ...(nameZh.value.trim() ? { 'zh-CN': nameZh.value.trim() } : {}),
    },
    aliases: {
      ...(aliasesEn.value.trim() ? { en: splitAliases(aliasesEn.value) } : {}),
      ...(aliasesZh.value.trim() ? { 'zh-CN': splitAliases(aliasesZh.value) } : {}),
    },
    category: category.value.trim() || 'other',
    visualKey: visualKey.value,
    baseUnit: baseUnit.value,
    packagePresets: presets.value
      .filter((preset) => preset.labelEn.trim() && preset.amount > 0)
      .map((preset) => ({
        label: {
          en: preset.labelEn.trim(),
          ...(preset.labelZh.trim() ? { 'zh-CN': preset.labelZh.trim() } : {}),
        },
        amount: String(preset.amount),
        unit: preset.unit,
      })),
    recommendedStorage: recommendedStorage.value,
    active: active.value,
    shelfLife,
  }
}

async function save() {
  error.value = ''
  if (!nameEn.value.trim()) {
    error.value = t('admin.errors.nameRequired')
    return
  }
  saving.value = true
  try {
    if (isEditing.value) {
      await updateFoodDefinition(foodKey.value, buildPayload())
    } else {
      await createFoodDefinition(buildPayload())
    }
    await hydrateLibrary(true)
    await router.push({ name: 'admin' })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : t('admin.errors.generic')
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!isEditing.value) return
  const confirmed = window.confirm(t('admin.foods.confirmDelete', { name: nameEn.value }))
  if (!confirmed) return
  try {
    await deleteFoodDefinition(foodKey.value)
    await hydrateLibrary(true)
    await router.push({ name: 'admin' })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : t('admin.errors.generic')
  }
}

const previewName = computed(() => nameEn.value.trim() || t('admin.editor.previewName'))

/** Uploads a custom icon immediately (independent of the form's Save action). */
async function onIconFilePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !isEditing.value) return
  iconError.value = ''
  iconUploading.value = true
  try {
    const updated = await uploadFoodIcon(foodKey.value, file)
    customIcon.value = updated.customIcon
    if (updated.customIcon) registerCustomIcon(foodKey.value, updated.customIcon)
    await hydrateLibrary(true)
  } catch (cause) {
    iconError.value = cause instanceof Error ? cause.message : t('admin.errors.iconUploadFailed')
  } finally {
    iconUploading.value = false
  }
}

async function removeIcon() {
  if (!isEditing.value) return
  iconError.value = ''
  try {
    await removeFoodIcon(foodKey.value)
    customIcon.value = null
    await hydrateLibrary(true)
  } catch (cause) {
    iconError.value = cause instanceof Error ? cause.message : t('admin.errors.iconUploadFailed')
  }
}
</script>

<template>
  <div class="admin-editor">
    <AppTaskHeader :title="title" :back-label="t('common.back')" @back="router.push({ name: 'admin' })" />

    <main v-if="notFound" class="admin-editor__content">
      <p class="admin-editor__error" role="alert">{{ t('admin.errors.foodNotFound') }}</p>
      <AppButton variant="secondary" @click="router.push({ name: 'admin' })">{{ t('common.back') }}</AppButton>
    </main>

    <main v-else-if="loading" class="admin-editor__content">
      <p class="admin-editor__muted">{{ t('admin.foods.loading') }}</p>
    </main>

    <form v-else class="admin-editor__content" @submit.prevent="save">
      <section class="form-card">
        <h2>{{ t('admin.editor.identity') }}</h2>
        <label class="form-field">
          <span class="field-label">{{ t('admin.editor.nameEn') }} *</span>
          <input v-model="nameEn" class="text-input" type="text" required>
        </label>
        <label class="form-field">
          <span class="field-label">{{ t('admin.editor.nameZh') }}</span>
          <input v-model="nameZh" class="text-input" type="text">
        </label>
        <div class="form-row">
          <label class="form-field">
            <span class="field-label">{{ t('admin.editor.aliasesEn') }}</span>
            <input v-model="aliasesEn" class="text-input" type="text" :placeholder="t('admin.editor.aliasesPlaceholder')">
          </label>
          <label class="form-field">
            <span class="field-label">{{ t('admin.editor.aliasesZh') }}</span>
            <input v-model="aliasesZh" class="text-input" type="text" :placeholder="t('admin.editor.aliasesPlaceholder')">
          </label>
        </div>
        <p class="form-hint">{{ t('admin.editor.aliasesHint') }}</p>
        <label class="form-field">
          <span class="field-label">{{ t('admin.editor.category') }}</span>
          <input v-model="category" class="text-input" type="text" list="admin-categories">
          <datalist id="admin-categories">
            <option v-for="item in categorySuggestions" :key="item" :value="item" />
          </datalist>
        </label>
        <label class="form-field form-field--check">
          <input v-model="active" type="checkbox">
          <span>{{ t('admin.editor.active') }}</span>
        </label>
      </section>

      <section class="form-card">
        <h2>{{ t('admin.editor.icon') }}</h2>
        <p class="form-hint">{{ t('admin.editor.iconHint') }}</p>

        <div v-if="customIcon" class="icon-uploaded">
          <img class="icon-uploaded__preview" :src="customIcon" alt="" width="56" height="56">
          <div class="icon-uploaded__copy">
            <strong>{{ t('admin.editor.iconUploaded') }}</strong>
            <button type="button" class="icon-uploaded__remove" @click="removeIcon">
              {{ t('admin.editor.iconRemove') }}
            </button>
          </div>
        </div>

        <div v-if="isEditing" class="icon-upload">
          <label class="icon-upload__button">
            <span v-if="iconUploading">{{ t('admin.editor.iconUploading') }}</span>
            <span v-else>{{ customIcon ? t('admin.editor.iconReplace') : t('admin.editor.iconUpload') }}</span>
            <input
              ref="iconInput"
              class="sr-only"
              type="file"
              accept=".svg,.png,image/svg+xml,image/png"
              :disabled="iconUploading"
              @change="onIconFilePicked"
            >
          </label>
          <p class="form-hint icon-upload__spec">{{ t('admin.editor.iconSpec') }}</p>
        </div>
        <p v-else class="form-hint">{{ t('admin.editor.iconUploadAfterSave') }}</p>
        <p v-if="iconError" class="icon-upload__error" role="alert">{{ iconError }}</p>

        <div class="icon-grid" role="radiogroup" :aria-label="t('admin.editor.icon')">
          <button
            type="button"
            class="icon-option"
            :class="{ 'icon-option--selected': visualKey === '' }"
            :aria-pressed="visualKey === ''"
            @click="visualKey = ''"
          >
            <FoodToken :food-key="''" :name="previewName" :size="44" />
            <span>{{ t('admin.editor.iconAuto') }}</span>
          </button>
          <button
            v-for="key in iconKeys"
            :key="key"
            type="button"
            class="icon-option"
            :class="{ 'icon-option--selected': visualKey === key }"
            :aria-pressed="visualKey === key"
            :aria-label="t('admin.editor.iconPick', { name: key })"
            @click="visualKey = key"
          >
            <FoodToken :food-key="key" :name="key" :size="44" />
          </button>
        </div>
      </section>

      <section class="form-card">
        <h2>{{ t('admin.editor.storage') }}</h2>
        <div class="form-row">
          <label class="form-field">
            <span class="field-label">{{ t('admin.editor.baseUnit') }}</span>
            <select v-model="baseUnit" class="text-input">
              <option v-for="unit in inventoryUnits" :key="unit" :value="unit">{{ t(`units.${unit}`, 1) }}</option>
            </select>
          </label>
          <label class="form-field">
            <span class="field-label">{{ t('admin.editor.recommendedStorage') }}</span>
            <select v-model="recommendedStorage" class="text-input">
              <option value="FRIDGE">{{ t('storage.scopes.fridge') }}</option>
              <option value="FREEZER">{{ t('storage.scopes.freezer') }}</option>
              <option value="PANTRY">{{ t('storage.scopes.pantry') }}</option>
            </select>
          </label>
        </div>
        <p class="form-hint">{{ t('admin.editor.shelfLifeHint') }}</p>
        <div class="form-row">
          <label v-for="location in ['FRIDGE', 'FREEZER', 'PANTRY'] as const" :key="location" class="form-field">
            <span class="field-label">{{ t(`storage.scopes.${location.toLocaleLowerCase()}`) }}</span>
            <input
              v-model="shelfLifeDays[location]"
              class="text-input"
              type="number"
              min="0"
              max="3650"
              step="1"
              :placeholder="t('admin.editor.daysPlaceholder')"
            >
          </label>
        </div>
      </section>

      <section class="form-card">
        <h2>{{ t('admin.editor.presets') }}</h2>
        <p class="form-hint">{{ t('admin.editor.presetsHint') }}</p>
        <div v-if="presets.length" class="preset-list">
          <div v-for="(preset, index) in presets" :key="index" class="preset-row">
            <input v-model="preset.labelEn" class="text-input" type="text" :aria-label="t('admin.editor.presetLabelEn')" :placeholder="t('admin.editor.presetLabelEn')">
            <input v-model="preset.labelZh" class="text-input" type="text" :aria-label="t('admin.editor.presetLabelZh')" :placeholder="t('admin.editor.presetLabelZh')">
            <input v-model.number="preset.amount" class="text-input" type="number" min="0.01" step="0.01" :aria-label="t('admin.editor.presetAmount')">
            <select v-model="preset.unit" class="text-input" :aria-label="t('admin.editor.presetUnit')">
              <option v-for="unit in inventoryUnits" :key="unit" :value="unit">{{ t(`units.${unit}`, 1) }}</option>
            </select>
            <button
              type="button"
              class="preset-remove"
              :aria-label="t('admin.editor.removePreset', { index: index + 1 })"
              @click="removePreset(index)"
            >
              ✕
            </button>
          </div>
        </div>
        <AppButton size="small" variant="secondary" @click="addPreset">
          {{ t('admin.editor.addPreset') }}
        </AppButton>
      </section>

      <p v-if="error" class="admin-editor__error" role="alert">{{ error }}</p>

      <footer class="editor-actions">
        <AppButton v-if="isEditing" variant="ghost" @click="remove">
          {{ t('admin.foods.delete') }}
        </AppButton>
        <AppButton block :disabled="saving" type="submit">
          {{ saving ? t('admin.editor.saving') : t('admin.editor.save') }}
        </AppButton>
      </footer>
    </form>
  </div>
</template>

<style scoped>
.admin-editor {
  min-height: 100vh;
  background: var(--color-canvas);
}

.admin-editor__content {
  display: grid;
  width: min(100%, 720px);
  gap: var(--space-4);
  padding: var(--space-5) var(--space-3) 96px;
  margin: 0 auto;
}

.form-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.form-card h2 {
  font-size: var(--font-size-lg);
}

.form-hint {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.form-field {
  display: grid;
  gap: var(--space-1);
}

.form-field--check {
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.form-field--check input {
  width: 20px;
  height: 20px;
  accent-color: var(--color-primary);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.text-input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.icon-uploaded {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface-sunken);
}

.icon-uploaded__preview {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  object-fit: contain;
}

.icon-uploaded__copy {
  display: grid;
  gap: var(--space-1);
}

.icon-uploaded__remove {
  justify-self: start;
  min-height: 32px;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  color: var(--color-danger);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.icon-uploaded__remove:hover {
  background: var(--color-danger-soft);
}

.icon-upload {
  display: grid;
  gap: var(--space-1);
}

.icon-upload__button {
  display: inline-flex;
  min-height: var(--tap-target-min);
  align-items: center;
  justify-content: center;
  justify-self: start;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.icon-upload__button:hover {
  background: var(--color-primary-softer);
}

.icon-upload__spec {
  max-width: 42ch;
  line-height: var(--line-height-normal);
}

.icon-upload__error {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  background: var(--color-danger-soft);
  font-size: var(--font-size-xs);
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
  gap: var(--space-2);
}

.icon-option {
  display: flex;
  min-height: 84px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.icon-option--selected {
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-sm);
}

.preset-list {
  display: grid;
  gap: var(--space-2);
}

.preset-row {
  display: grid;
  grid-template-columns: 1fr 1fr 96px 84px 36px;
  gap: var(--space-2);
  align-items: center;
}

.preset-remove {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: var(--radius-md);
  color: var(--color-danger);
}

.preset-remove:hover {
  background: var(--color-danger-soft);
}

.admin-editor__error {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  background: var(--color-danger-soft);
  font-size: var(--font-size-sm);
}

.admin-editor__muted {
  color: var(--color-muted);
  text-align: center;
}

.editor-actions {
  position: fixed;
  z-index: var(--z-sticky);
  right: 0;
  bottom: 0;
  left: 0;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-2);
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

@media (max-width: 620px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .preset-row {
    grid-template-columns: 1fr 1fr 84px 72px 36px;
  }
}
</style>
