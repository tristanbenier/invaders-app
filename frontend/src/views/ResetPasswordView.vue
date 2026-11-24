<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { authApi } from '@/api/endpoints'
import type { PublicPasswordReset } from '@/api/types'
import FieldErrors from '@/components/FieldErrors.vue'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'

/** Page of the single-use link an admin created for a member who forgot their password. */
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const token = String(route.params.token)
const { errors, capture, clear } = useFormErrors()

const reset = ref<PublicPasswordReset | null>(null)
const loadError = ref<string | null>(null)
const password = ref('')
const confirmation = ref('')
const submitting = ref(false)

onMounted(async () => {
  if (auth.isAuthenticated) return
  try {
    reset.value = await authApi.passwordReset(token)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : String(error)
  }
})

async function submit() {
  clear()
  if (password.value !== confirmation.value) {
    errors.value = { confirmation: ['Les deux mots de passe ne correspondent pas.'] }
    return
  }
  submitting.value = true
  try {
    await auth.resetPassword(token, password.value)
    await router.replace('/')
  } catch (error) {
    capture(error)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page reset">
    <div v-if="auth.isAuthenticated" class="card">
      <p>Vous êtes déjà connecté. Déconnectez-vous pour utiliser ce lien.</p>
      <RouterLink to="/" class="btn btn--block">Aller à la carte</RouterLink>
    </div>

    <div v-else-if="loadError" class="card">
      <h1>Lien invalide</h1>
      <p class="muted">{{ loadError }} Demandez un nouveau lien à un administrateur de votre équipe.</p>
      <RouterLink to="/login" class="btn btn--block">Se connecter</RouterLink>
    </div>

    <template v-else-if="reset">
      <header>
        <h1>Nouveau mot de passe</h1>
        <p class="muted">Bonjour {{ reset.display_name }}, choisissez un nouveau mot de passe pour {{ reset.email }}.</p>
      </header>

      <form class="card reset__form" @submit.prevent="submit">
        <!-- Lets password managers save the new password for the right account. -->
        <input type="email" :value="reset.email" autocomplete="username" hidden readonly />
        <label class="field">
          <span>Nouveau mot de passe</span>
          <input v-model="password" class="input" type="password" autocomplete="new-password" required />
          <FieldErrors :messages="errors.password" />
        </label>
        <label class="field">
          <span>Confirmation</span>
          <input v-model="confirmation" class="input" type="password" autocomplete="new-password" required />
          <FieldErrors :messages="errors.confirmation" />
        </label>
        <FieldErrors :messages="[...(errors._ ?? []), ...(errors.token ?? [])]" />
        <button class="btn btn--primary btn--block" type="submit" :disabled="submitting">Enregistrer et se connecter</button>
      </form>
    </template>

    <p v-else class="muted">Chargement…</p>
  </div>
</template>

<style scoped>
.reset {
  min-height: 100%;
  justify-content: center;
}

.reset header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reset__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
