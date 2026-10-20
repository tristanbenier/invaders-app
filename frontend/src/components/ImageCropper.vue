<script setup lang="ts">
import 'cropperjs/dist/cropper.css'

import Cropper from 'cropperjs'
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import AppIcon from './AppIcon.vue'
import BottomSheet from './BottomSheet.vue'

/** Square crop of a picked photo; emits the cropped JPEG file. */
const props = defineProps<{ file: File }>()
const emit = defineEmits<{ done: [file: File]; cancel: [] }>()

// Same size as the server limit: no point sending more pixels.
const OUTPUT_SIZE = 1200

const areaElement = ref<HTMLElement>()
const imageElement = ref<HTMLImageElement>()
const sourceUrl = URL.createObjectURL(props.file)
const ready = ref(false)
const busy = ref(false)
const error = ref<string | null>(null)
let cropper: Cropper | undefined
let observer: ResizeObserver | undefined
let measuredWidth = 0

function createCropper() {
  cropper?.destroy()
  ready.value = false
  cropper = new Cropper(imageElement.value!, {
    aspectRatio: 1,
    viewMode: 1,
    dragMode: 'move',
    autoCropArea: 1,
    background: false,
    guides: false,
    // Resizes are handled below by recreating the cropper.
    responsive: false,
    toggleDragModeOnDblclick: false,
    ready: () => (ready.value = true),
  })
}

// Cropper.js measures its container only once: recreate it when the area changes width
// (modal layout settling, phone rotation).
function syncSize() {
  const width = areaElement.value?.offsetWidth ?? 0
  if (width > 0 && width !== measuredWidth) {
    measuredWidth = width
    createCropper()
  }
}

onMounted(async () => {
  await nextTick()
  syncSize()
  observer = new ResizeObserver(syncSize)
  observer.observe(areaElement.value!)
  window.addEventListener('resize', syncSize)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener('resize', syncSize)
  cropper?.destroy()
  URL.revokeObjectURL(sourceUrl)
})

function rotate() {
  cropper?.rotate(90)
}

function confirm() {
  if (!cropper) return
  busy.value = true
  const canvas = cropper.getCroppedCanvas({
    width: OUTPUT_SIZE,
    height: OUTPUT_SIZE,
    imageSmoothingQuality: 'high',
    fillColor: '#fff',
  })
  canvas.toBlob(
    (blob) => {
      busy.value = false
      if (!blob) {
        error.value = "Impossible de recadrer cette image. Essayez avec une autre photo."
        return
      }
      const name = props.file.name.replace(/\.[^.]+$/, '') || 'photo'
      emit('done', new File([blob], `${name}.jpg`, { type: 'image/jpeg' }))
    },
    'image/jpeg',
    0.9,
  )
}
</script>

<template>
  <BottomSheet title="Recadrer la photo" modal @close="emit('cancel')">
    <div class="cropper">
      <p class="muted cropper__hint">Déplacez et zoomez la photo pour cadrer l'invader. Le format est carré.</p>
      <div ref="areaElement" class="cropper__area">
        <img ref="imageElement" :src="sourceUrl" alt="Photo à recadrer" class="cropper__image" />
      </div>
      <p v-if="error" class="errors">{{ error }}</p>
      <div class="cropper__actions">
        <button type="button" class="btn btn--icon" aria-label="Pivoter de 90°" title="Pivoter" :disabled="!ready" @click="rotate">
          <AppIcon name="rotate" />
        </button>
        <button type="button" class="btn" @click="emit('cancel')">Annuler</button>
        <button type="button" class="btn btn--primary" :disabled="!ready || busy" @click="confirm">Valider</button>
      </div>
    </div>
  </BottomSheet>
</template>

<style scoped>
.cropper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cropper__hint {
  margin: 0;
  font-size: 0.85rem;
}

.cropper__area {
  height: min(60vh, 420px);
  background: var(--bg);
  border-radius: 10px;
  overflow: hidden;
}

/* Cropper.js needs a block image with max-width: 100%. */
.cropper__image {
  display: block;
  max-width: 100%;
}

.cropper__actions {
  display: flex;
  gap: 8px;
}

.cropper__actions .btn:not(.btn--icon) {
  flex: 1;
}
</style>
