<script setup lang="ts">
import { ref } from 'vue'

import FieldErrors from '@/components/FieldErrors.vue'
import { authApi } from '@/api/endpoints'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const { errors, capture, clear } = useFormErrors()
const flashInvadersUid = ref('')
// The saved UID, fetched only when the member asks to see it.
const savedUid = ref<string | null>(null)
const busy = ref(false)

async function run(action: () => Promise<unknown>) {
  clear()
  busy.value = true
  try {
    await action()
  } catch (error) {
    capture(error)
  } finally {
    busy.value = false
  }
}

const enableFlashSync = () =>
  run(async () => {
    await auth.setFlashInvadersUid(flashInvadersUid.value.trim())
    flashInvadersUid.value = ''
  })

const toggleManualFlash = (event: Event) =>
  run(() => auth.setManualFlash((event.target as HTMLInputElement).checked))

function disableFlashSync() {
  if (!window.confirm('Désactiver la synchro ? Votre UID sera effacé.')) return
  run(async () => {
    await auth.setFlashInvadersUid('')
    savedUid.value = null
  })
}

function toggleUid() {
  if (savedUid.value !== null) savedUid.value = null
  else run(async () => (savedUid.value = (await authApi.flashInvadersUid()).uid))
}
</script>

<template>
  <div class="page settings">
    <h1>Réglages</h1>

    <section class="card settings__section">
      <h2>Synchro Flash Invaders</h2>
      <template v-if="auth.me?.flash_sync_enabled">
        <p class="muted">Active : les invaders flashés dans l'app Flash Invaders sont cochés ici automatiquement (vérification chaque minute tant que l'app est ouverte).</p>
        <label class="settings__check-row">
          <input type="checkbox" :checked="auth.me.manual_flash" :disabled="busy" @change="toggleManualFlash" />
          <span>Garder les boutons « Je l'ai flashé » et « Annuler mon flash » (utile si la synchro ne marche plus)</span>
        </label>
        <div class="settings__uid">
          <button type="button" class="btn" :disabled="busy" @click="toggleUid">
            {{ savedUid === null ? "Voir l'UID" : "Masquer l'UID" }}
          </button>
          <code v-if="savedUid !== null" class="settings__uid-value">{{ savedUid }}</code>
        </div>
        <button type="button" class="btn" :disabled="busy" @click="disableFlashSync">Désactiver la synchro</button>
      </template>
      <template v-else>
        <p class="muted">Indiquez l'UID de votre compte Flash Invaders pour cocher automatiquement vos flashs. Il reste privé : vous seul pourrez l'afficher ici.</p>
        <form class="settings__form" @submit.prevent="enableFlashSync">
          <input
            v-model="flashInvadersUid"
            class="input"
            type="password"
            autocomplete="off"
            spellcheck="false"
            placeholder="UID Flash Invaders"
            aria-label="UID Flash Invaders"
            required
          />
          <button type="submit" class="btn btn--primary" :disabled="busy || !flashInvadersUid.trim()">Activer</button>
        </form>
        <FieldErrors :messages="errors.flash_invaders_uid ?? []" />
      </template>
      <FieldErrors :messages="errors._ ?? []" />
    </section>

  </div>
</template>

<style scoped>
.settings__section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.settings__section h2 {
  font-size: 1.05rem;
}

.settings__section p {
  margin: 0;
  font-size: 0.9rem;
}

.settings__check-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.9rem;
}

.settings__check-row input {
  margin-top: 3px;
}

.settings__uid {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.settings__uid-value {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  overflow-wrap: anywhere;
  user-select: all;
}

.settings__form {
  display: flex;
  gap: 8px;
}

.settings__form .btn {
  white-space: nowrap;
}
</style>
