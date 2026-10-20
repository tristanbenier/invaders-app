<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { authApi } from '@/api/endpoints'
import type { PublicInvitation } from '@/api/types'
import FieldErrors from '@/components/FieldErrors.vue'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const token = String(route.params.token)
const { errors, capture, clear } = useFormErrors()

const invitation = ref<PublicInvitation | null>(null)
const loadError = ref<string | null>(null)
const form = ref({ email: '', display_name: '', password: '' })
const submitting = ref(false)

onMounted(async () => {
  try {
    invitation.value = await authApi.invitation(token)
    form.value.email = invitation.value.email
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : String(error)
  }
})

async function submit() {
  clear()
  submitting.value = true
  try {
    await auth.acceptInvitation({ token, ...form.value })
    await router.replace('/')
  } catch (error) {
    capture(error)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page invitation">
    <div v-if="auth.isAuthenticated" class="card">
      <p>Vous êtes déjà connecté. Déconnectez-vous pour utiliser cette invitation.</p>
      <RouterLink to="/" class="btn btn--block">Aller à la carte</RouterLink>
    </div>

    <div v-else-if="loadError" class="card">
      <h1>Invitation invalide</h1>
      <p class="muted">{{ loadError }}</p>
      <RouterLink to="/login" class="btn btn--block">Se connecter</RouterLink>
    </div>

    <template v-else-if="invitation">
      <header>
        <h1>Rejoindre « {{ invitation.team.name }} »</h1>
        <p class="muted">
          <template v-if="invitation.invited_by">{{ invitation.invited_by }} vous invite à rejoindre son équipe.</template>
          Créez votre compte pour accéder à la carte.
        </p>
      </header>

      <form class="card invitation__form" @submit.prevent="submit">
        <label class="field">
          <span>Email</span>
          <input
            v-model="form.email"
            class="input"
            type="email"
            autocomplete="email"
            required
            :readonly="Boolean(invitation.email)"
          />
          <FieldErrors :messages="errors.email" />
        </label>
        <label class="field">
          <span>Pseudo</span>
          <input v-model="form.display_name" class="input" maxlength="50" autocomplete="nickname" required />
          <FieldErrors :messages="errors.display_name" />
        </label>
        <label class="field">
          <span>Mot de passe</span>
          <input v-model="form.password" class="input" type="password" autocomplete="new-password" required />
          <FieldErrors :messages="errors.password" />
        </label>
        <FieldErrors :messages="[...(errors._ ?? []), ...(errors.token ?? [])]" />
        <button class="btn btn--primary btn--block" type="submit" :disabled="submitting">Créer mon compte</button>
      </form>
    </template>
  </div>
</template>

<style scoped>
.invitation {
  min-height: 100%;
  justify-content: center;
}

.invitation header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.invitation__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
