<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { teamApi } from '@/api/endpoints'
import type { Invitation, Member } from '@/api/types'
import AppIcon from '@/components/AppIcon.vue'
import FieldErrors from '@/components/FieldErrors.vue'
import { formatDate } from '@/composables/format'
import { useFormErrors } from '@/composables/useFormErrors'
import { useAuthStore } from '@/stores/auth'
import { useTeamStore } from '@/stores/team'

const auth = useAuthStore()
const teamStore = useTeamStore()
const router = useRouter()
const { errors, capture, clear } = useFormErrors()

const invitations = ref<Invitation[]>([])
const inviteEmail = ref('')
const copiedId = ref<number | null>(null)
const flashInvadersUid = ref('')
const busy = ref(false)

async function load() {
  try {
    await Promise.all([teamStore.load(), teamApi.invitations().then((list) => (invitations.value = list))])
  } catch (error) {
    capture(error)
  }
}

onMounted(load)

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

const invite = () =>
  run(async () => {
    const invitation = await teamApi.invite(inviteEmail.value.trim())
    invitations.value = [invitation, ...invitations.value]
    inviteEmail.value = ''
    await copy(invitation)
  })

async function copy(invitation: Invitation) {
  try {
    await navigator.clipboard.writeText(invitation.url)
    copiedId.value = invitation.id
    setTimeout(() => copiedId.value === invitation.id && (copiedId.value = null), 2000)
  } catch {
    window.prompt('Copiez le lien :', invitation.url)
  }
}

const revoke = (invitation: Invitation) =>
  run(async () => {
    await teamApi.revokeInvitation(invitation.id)
    invitations.value = invitations.value.filter((item) => item.id !== invitation.id)
  })

function removeMember(member: Member) {
  if (!window.confirm(`Retirer ${member.display_name} de l'équipe ? Son compte sera désactivé.`)) return
  run(async () => {
    await teamApi.removeMember(member.id)
    await teamStore.load()
  })
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
  run(() => auth.setFlashInvadersUid(''))
}

const logout = () =>
  run(async () => {
    await auth.logout()
    await router.replace({ name: 'login' })
  })
</script>

<template>
  <div class="page team">
    <header class="team__header">
      <div>
        <h1>{{ teamStore.team?.name ?? auth.me?.team.name }}</h1>
        <p class="muted">Connecté en tant que {{ auth.me?.display_name }}</p>
      </div>
      <button type="button" class="btn btn--icon" aria-label="Se déconnecter" :disabled="busy" @click="logout">
        <AppIcon name="logout" />
      </button>
    </header>

    <FieldErrors :messages="[...(errors._ ?? []), ...(errors.email ?? [])]" />

    <section class="card team__section">
      <h2>Synchro Flash Invaders</h2>
      <template v-if="auth.me?.flash_sync_enabled">
        <p class="muted">Active : les invaders flashés dans l'app Flash Invaders sont cochés ici automatiquement (vérification chaque minute tant que l'app est ouverte).</p>
        <label class="team__check">
          <input type="checkbox" :checked="auth.me.manual_flash" :disabled="busy" @change="toggleManualFlash" />
          <span>Garder les boutons « Je l'ai flashé » et « Annuler mon flash » (utile si la synchro ne marche plus)</span>
        </label>
        <button type="button" class="btn" :disabled="busy" @click="disableFlashSync">Désactiver la synchro</button>
      </template>
      <template v-else>
        <p class="muted">Indiquez l'UID de votre compte Flash Invaders pour cocher automatiquement vos flashs. Il reste secret : personne, vous compris, ne pourra le relire ici.</p>
        <form class="team__invite" @submit.prevent="enableFlashSync">
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
    </section>

    <section class="card team__section">
      <h2>Membres ({{ teamStore.team?.members.length ?? 0 }})</h2>
      <ul class="team__list">
        <li v-for="member in teamStore.team?.members ?? []" :key="member.id">
          <div class="team__item-text">
            <span>{{ member.display_name }}<template v-if="member.id === auth.me?.id"> (vous)</template></span>
            <small class="muted">
              {{ member.role === 'admin' ? 'Administrateur' : 'Membre' }} · depuis le {{ formatDate(member.date_joined) }}
            </small>
          </div>
          <button
            v-if="auth.isAdmin && member.id !== auth.me?.id"
            type="button"
            class="btn btn--icon btn--danger"
            :aria-label="`Retirer ${member.display_name}`"
            :disabled="busy"
            @click="removeMember(member)"
          >
            <AppIcon name="trash" :size="18" />
          </button>
        </li>
      </ul>
    </section>

    <section class="card team__section">
      <h2>Inviter un membre</h2>
      <p class="muted">Le lien est valable 7 jours et ne sert qu'une fois. L'email est facultatif : s'il est indiqué, seule cette adresse pourra l'utiliser.</p>
      <form class="team__invite" @submit.prevent="invite">
        <input v-model="inviteEmail" class="input" type="email" placeholder="Email (facultatif)" aria-label="Email de l'invité" />
        <button type="submit" class="btn btn--primary" :disabled="busy">Créer le lien</button>
      </form>

      <ul v-if="invitations.length" class="team__list">
        <li v-for="invitation in invitations" :key="invitation.id">
          <div class="team__item-text">
            <span>{{ invitation.email || 'Lien ouvert' }}</span>
            <small class="muted">Expire le {{ formatDate(invitation.expires_at) }}</small>
          </div>
          <button type="button" class="btn btn--icon" aria-label="Copier le lien" @click="copy(invitation)">
            <AppIcon :name="copiedId === invitation.id ? 'check' : 'copy'" :size="18" />
          </button>
          <button
            v-if="auth.isAdmin || invitation.invited_by?.id === auth.me?.id"
            type="button"
            class="btn btn--icon btn--danger"
            aria-label="Révoquer l'invitation"
            :disabled="busy"
            @click="revoke(invitation)"
          >
            <AppIcon name="trash" :size="18" />
          </button>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.team__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.team__section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.team__section h2 {
  font-size: 1.05rem;
}

.team__section p {
  margin: 0;
  font-size: 0.9rem;
}

.team__check {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.9rem;
}

.team__check input {
  margin-top: 3px;
}

.team__invite {
  display: flex;
  gap: 8px;
}

.team__invite .btn {
  white-space: nowrap;
}

.team__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.team__list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-top: 1px solid var(--border);
}

.team__item-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-wrap: anywhere;
}
</style>
