<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import type { TimelinePoint } from '@/api/types'
import { formatDate, today } from '@/composables/format'

/** Cumulative score over time: single-series step area with a hover crosshair. */
const props = defineProps<{ points: TimelinePoint[] }>()

const HEIGHT = 200
const MARGIN = { top: 12, right: 12, bottom: 26, left: 44 }
const DAY = 86_400_000
const shortDate = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' })
const numberFormat = new Intl.NumberFormat('fr-FR')

const container = ref<HTMLElement>()
const width = ref(320)
const hoverIndex = ref<number | null>(null)
let resizeObserver: ResizeObserver | undefined

onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => entry && (width.value = entry.contentRect.width))
  if (container.value) resizeObserver.observe(container.value)
})
onBeforeUnmount(() => resizeObserver?.disconnect())

const toTime = (date: string) => new Date(`${date}T00:00:00`).getTime()

function niceStep(raw: number) {
  const power = 10 ** Math.floor(Math.log10(raw))
  const fraction = raw / power
  return (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10) * power
}

const chart = computed(() => {
  const data = props.points
  const innerWidth = Math.max(width.value - MARGIN.left - MARGIN.right, 50)
  const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom
  const first = toTime(data[0]!.date)
  // The score stays flat until today, and the axis spans at least a week.
  const last = Math.max(toTime(today()), first + 7 * DAY)
  const maxValue = data[data.length - 1]!.cumulative_points
  const step = niceStep(Math.max(maxValue, 1) / 4)
  const yMax = Math.ceil(Math.max(maxValue, 1) / step) * step

  const x = (time: number) => MARGIN.left + ((time - first) / (last - first)) * innerWidth
  const y = (value: number) => MARGIN.top + innerHeight - (value / yMax) * innerHeight
  const baseline = y(0)

  // Step line: the score jumps on each flash day and stays flat in between.
  const coords = data.map((point) => ({ x: x(toTime(point.date)), y: y(point.cumulative_points) }))
  let line = `M${MARGIN.left},${baseline} H${coords[0]!.x} V${coords[0]!.y}`
  for (const point of coords.slice(1)) line += ` H${point.x} V${point.y}`
  line += ` H${x(last)}`
  const area = `${line} V${baseline} H${MARGIN.left} Z`

  const yTicks = Array.from({ length: Math.round(yMax / step) + 1 }, (_, i) => ({ value: i * step, y: y(i * step) }))
  const xTickCount = innerWidth < 260 ? 3 : 4
  const xTicks = Array.from({ length: xTickCount }, (_, i) => {
    const time = first + ((last - first) * i) / (xTickCount - 1)
    return { label: shortDate.format(new Date(time)), x: x(time), anchor: i === 0 ? 'start' : i === xTickCount - 1 ? 'end' : 'middle' }
  })

  return { line, area, coords, yTicks, xTicks, baseline, innerWidth, x, first, last }
})

function onPointerMove(event: PointerEvent) {
  const svg = event.currentTarget as SVGSVGElement
  const offsetX = event.clientX - svg.getBoundingClientRect().left
  const { first, last, innerWidth } = chart.value
  const time = first + ((offsetX - MARGIN.left) / innerWidth) * (last - first)
  // Last flash day at or before the pointer.
  let index = 0
  props.points.forEach((point, i) => {
    if (toTime(point.date) <= time) index = i
  })
  hoverIndex.value = index
}

const hovered = computed(() => {
  if (hoverIndex.value === null) return null
  const point = props.points[hoverIndex.value]
  const coords = chart.value.coords[hoverIndex.value]
  if (!point || !coords) return null
  const left = Math.min(Math.max(coords.x, 80), width.value - 80)
  return { point, coords, left }
})
</script>

<template>
  <div ref="container" class="progress-chart">
    <svg
      :width="width"
      :height="HEIGHT"
      role="img"
      :aria-label="`Score cumulé : ${numberFormat.format(points[points.length - 1]?.cumulative_points ?? 0)} points`"
      @pointermove="onPointerMove"
      @pointerleave="hoverIndex = null"
    >
      <g class="progress-chart__grid">
        <line v-for="tick in chart.yTicks" :key="tick.value" :x1="MARGIN.left" :x2="width - MARGIN.right" :y1="tick.y" :y2="tick.y" />
      </g>
      <g class="progress-chart__axis">
        <text v-for="tick in chart.yTicks" :key="tick.value" :x="MARGIN.left - 8" :y="tick.y" text-anchor="end" dominant-baseline="middle">
          {{ numberFormat.format(tick.value) }}
        </text>
        <text v-for="tick in chart.xTicks" :key="tick.label + tick.x" :x="tick.x" :y="HEIGHT - 6" :text-anchor="tick.anchor">
          {{ tick.label }}
        </text>
      </g>
      <path :d="chart.area" class="progress-chart__area" />
      <path :d="chart.line" class="progress-chart__line" />
      <!-- End marker with a surface ring, plus the hovered point. -->
      <circle
        v-if="chart.coords.length"
        :cx="chart.coords[chart.coords.length - 1]!.x"
        :cy="chart.coords[chart.coords.length - 1]!.y"
        r="4"
        class="progress-chart__dot"
      />
      <template v-if="hovered">
        <line :x1="hovered.coords.x" :x2="hovered.coords.x" :y1="MARGIN.top" :y2="chart.baseline" class="progress-chart__crosshair" />
        <circle :cx="hovered.coords.x" :cy="hovered.coords.y" r="5" class="progress-chart__dot" />
      </template>
    </svg>

    <div v-if="hovered" class="progress-chart__tooltip" :style="{ left: `${hovered.left}px` }">
      <strong>{{ formatDate(hovered.point.date) }}</strong>
      <span>{{ numberFormat.format(hovered.point.cumulative_points) }} points au total</span>
      <span class="muted">
        +{{ hovered.point.points }} pts · {{ hovered.point.flashes }} flash{{ hovered.point.flashes > 1 ? 's' : '' }} ce jour-là
      </span>
    </div>
  </div>
</template>

<style scoped>
.progress-chart {
  position: relative;
  width: 100%;
}

.progress-chart svg {
  display: block;
  touch-action: pan-y;
}

.progress-chart__grid line {
  stroke: var(--border);
  stroke-width: 1;
}

.progress-chart__axis text {
  fill: var(--muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.progress-chart__area {
  fill: var(--accent);
  fill-opacity: 0.1;
}

.progress-chart__line {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.progress-chart__dot {
  fill: var(--accent);
  stroke: var(--surface);
  stroke-width: 2;
}

.progress-chart__crosshair {
  stroke: var(--muted);
  stroke-width: 1;
}

.progress-chart__tooltip {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-2);
  box-shadow: var(--shadow);
  font-size: 0.8rem;
  white-space: nowrap;
  pointer-events: none;
}
</style>
