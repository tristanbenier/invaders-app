<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import FieldErrors from '@/components/FieldErrors.vue'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { errors, capture, clear } = useFormErrors()

const email = ref('')
const password = ref('')
const submitting = ref(false)

async function submit() {
  clear()
  submitting.value = true
  try {
    await auth.login(email.value, password.value)
    const next = typeof route.query.next === 'string' && route.query.next.startsWith('/') ? route.query.next : '/'
    await router.replace(next)
  } catch (error) {
    capture(error)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page auth">
    <header class="auth__header">
      <img src="/favicon.svg" alt="" width="56" height="41" class="auth__logo" />
      <h1>Invaders</h1>
      <p class="muted">La carte des Space Invaders de votre équipe.</p>
    </header>

    <form class="card auth__form" @submit.prevent="submit">
      <label class="field">
        <span>Email</span>
        <input v-model="email" class="input" type="email" autocomplete="email" required />
        <FieldErrors :messages="errors.email" />
      </label>
      <label class="field">
        <span>Mot de passe</span>
        <input v-model="password" class="input" type="password" autocomplete="current-password" required />
        <FieldErrors :messages="errors.password" />
      </label>
      <FieldErrors :messages="errors._" />
      <button class="btn btn--primary btn--block" type="submit" :disabled="submitting">Se connecter</button>
    </form>

    <p class="muted auth__hint">Pas de compte ? Demandez un lien d'invitation à un membre de votre équipe.</p>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100%;
  justify-content: center;
}

.auth__header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.auth__logo {
  image-rendering: pixelated;
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.auth__hint {
  text-align: center;
  font-size: 0.9rem;
}
</style>
