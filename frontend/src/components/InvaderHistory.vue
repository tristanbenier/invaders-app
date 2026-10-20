<script setup lang="ts">
import { ref, watch } from 'vue'

import { invadersApi } from '@/api/endpoints'
import { type HistoryEntry, STATUS_LABELS, type Status } from '@/api/types'
import { distanceMeters, formatDistance } from '@/composables/distance'

// lat/lng: current position, used for the coordinate an entry did not change.
const props = defineProps<{ invaderId: number; updatedAt: string; lat: number; lng: number }>()

const ACTION_LABELS = { created: 'Ajouté', updated: 'Modifié', imported: 'Importé' } as const
const dateTime = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

const open = ref(false)
const entries = ref<HistoryEntry[] | null>(null)
const error = ref<string | null>(null)

async function load() {
  error.value = null
  try {
    entries.value = await invadersApi.history(props.invaderId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

function toggle() {
  open.value = !open.value
  if (open.value && entries.value === null) load()
}

// Reload when the invader changes (another invader, or an edit made from the sheet).
watch(
  () => [props.invaderId, props.updatedAt],
  () => {
    entries.value = null
    if (open.value) load()
  },
)

/** Human-readable lines for one entry, in French. */
function describe(entry: HistoryEntry): string[] {
  const { changes } = entry
  const lines: string[] = []
  if (changes.name) lines.push(`Nom : ${changes.name.old} → ${changes.name.new}`)
  if (changes.status) {
    lines.push(`Statut : ${STATUS_LABELS[changes.status.old as Status]} → ${STATUS_LABELS[changes.status.new as Status]}`)
  }
  if (changes.points) lines.push(`Points : ${changes.points.old} → ${changes.points.new}`)
  if (changes.lat || changes.lng) {
    const before = { lat: Number(changes.lat?.old ?? props.lat), lng: Number(changes.lng?.old ?? props.lng) }
    const after = { lat: Number(changes.lat?.new ?? props.lat), lng: Number(changes.lng?.new ?? props.lng) }
    const moved = distanceMeters(before, after)
    lines.push(moved >= 1 ? `Déplacé d'environ ${formatDistance(moved)}` : 'Position ajustée')
  }
  if (changes.address1 || changes.address2 || changes.zip) lines.push('Adresse modifiée')
  if (changes.comment) lines.push(changes.comment.new ? (changes.comment.old ? 'Commentaire modifié' : 'Commentaire ajouté') : 'Commentaire retiré')
  if (changes.image) lines.push(changes.image.new ? (changes.image.old ? 'Photo remplacée' : 'Photo ajoutée') : 'Photo retirée')
  return lines
}
</script>

<template>
  <section class="history">
    <button type="button" class="history__toggle" :aria-expanded="open" @click="toggle">
      Historique des modifications
      <span aria-hidden="true">{{ open ? '▴' : '▾' }}</span>
    </button>
    <template v-if="open">
      <p v-if="error" class="errors">{{ error }}</p>
      <p v-else-if="entries === null" class="muted">Chargement…</p>
      <p v-else-if="!entries.length" class="muted">Aucune modification enregistrée.</p>
      <ol v-else class="history__list">
        <li v-for="entry in entries" :key="entry.id">
          <div class="history__meta">
            <strong>{{ ACTION_LABELS[entry.action] }}</strong>
            <span class="muted">
              par {{ entry.user?.display_name ?? 'un ancien membre' }} · {{ dateTime.format(new Date(entry.created_at)) }}
            </span>
          </div>
          <ul v-if="describe(entry).length" class="history__changes">
            <li v-for="line in describe(entry)" :key="line">{{ line }}</li>
          </ul>
        </li>
      </ol>
    </template>
  </section>
</template>

<style scoped>
.history__toggle {
  display: flex;
  justify-content: space-between;
  width: 100%;
  min-height: 44px;
  padding: 0;
  border: none;
  background: transparent;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
}

.history__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.history__list > li {
  padding: 8px 0;
  border-top: 1px solid var(--border);
}

.history__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  font-size: 0.9rem;
}

.history__meta .muted {
  font-size: 0.8rem;
}

.history__changes {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 0.85rem;
}
</style>
