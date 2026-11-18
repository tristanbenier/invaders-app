<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import type { MemberTimeline } from '@/api/types'
import { formatDate, today } from '@/composables/format'

/**
 * Cumulative score over time, one step line per member, with a legend and a hover crosshair
 * listing every member's score at that date.
 */
const props = defineProps<{ timelines: MemberTimeline[]; meId?: number }>()

// The current member keeps the app's green, opaque and drawn on top. The others get a hue
// each, slightly transparent, in the timelines' fixed (join) order so a member keeps their
// color. Dataviz reference dark steps minus green and aqua (too close to the accent), ordered
// so that neighbours stay apart (adjacent pairs validated on the card surface #1f1c2e).
const ME_COLOR = '#7cf29c'
const OTHER_COLORS = ['#e66767', '#9085e9', '#d95926', '#3987e5', '#d55181', '#c98500']
const OTHER_OPACITY = 0.65
const HEIGHT = 220
const MARGIN = { top: 12, right: 12, bottom: 26, left: 48 }
const DAY = 86_400_000
const shortDate = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short' })
// Over long spans, ticks are months of different years: the year matters more than the day.
const monthYear = new Intl.DateTimeFormat('fr-FR', { month: 'short', year: 'numeric' })
const numberFormat = new Intl.NumberFormat('fr-FR')

const container = ref<HTMLElement>()
const width = ref(320)
const hoverTime = ref<number | null>(null)
let resizeObserver: ResizeObserver | undefined

onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => entry && (width.value = entry.contentRect.width))
  if (container.value) resizeObserver.observe(container.value)
})
onBeforeUnmount(() => resizeObserver?.disconnect())

const toTime = (date: string) => new Date(`${date}T00:00:00`).getTime()
const localDate = (time: number) => {
  const date = new Date(time)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function niceStep(raw: number) {
  const power = 10 ** Math.floor(Math.log10(raw))
  const fraction = raw / power
  return (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10) * power
}

/** Members with at least one flash, each with its fixed color. */
const series = computed(() => {
  const others = props.timelines.filter((timeline) => timeline.user.id !== props.meId)
  const all = props.timelines
    .map((timeline) => {
      const isMe = timeline.user.id === props.meId
      const index = others.indexOf(timeline)
      return {
        id: timeline.user.id,
        name: timeline.user.display_name,
        isMe,
        color: isMe ? ME_COLOR : OTHER_COLORS[index % OTHER_COLORS.length]!,
        opacity: isMe ? 1 : OTHER_OPACITY,
        points: timeline.points.map((point) => ({ time: toTime(point.date), value: point.cumulative_points })),
      }
    })
    .filter((member) => member.points.length > 0)
  // Drawn last, so on top of the others.
  return [...all.filter((member) => !member.isMe), ...all.filter((member) => member.isMe)]
})
/** Legend order: the current member first, then the others in join order. */
const legend = computed(() => [...series.value.filter((member) => member.isMe), ...series.value.filter((member) => !member.isMe)])

/** A member's cumulative score at a given time (0 before their first flash). */
function valueAt(points: { time: number; value: number }[], time: number) {
  let value = 0
  for (const point of points) {
    if (point.time > time) break
    value = point.value
  }
  return value
}

const chart = computed(() => {
  const innerWidth = Math.max(width.value - MARGIN.left - MARGIN.right, 50)
  const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom
  const first = Math.min(...series.value.map((member) => member.points[0]!.time))
  // Scores stay flat until today, and the axis spans at least a week.
  const last = Math.max(toTime(today()), first + 7 * DAY)
  const maxValue = Math.max(...series.value.map((member) => member.points[member.points.length - 1]!.value), 1)
  const step = niceStep(maxValue / 4)
  const yMax = Math.ceil(maxValue / step) * step

  const x = (time: number) => MARGIN.left + ((time - first) / (last - first)) * innerWidth
  const y = (value: number) => MARGIN.top + innerHeight - (value / yMax) * innerHeight
  const baseline = y(0)

  // Step lines: a score jumps on each flash day and stays flat in between.
  const lines = series.value.map((member) => {
    const start = member.points[0]!
    let path = `M${x(start.time)},${baseline} V${y(start.value)}`
    for (const point of member.points.slice(1)) path += ` H${x(point.time)} V${y(point.value)}`
    const end = member.points[member.points.length - 1]!
    return { ...member, path: `${path} H${x(last)}`, endY: y(end.value), endValue: end.value }
  })

  const yTicks = Array.from({ length: Math.round(yMax / step) + 1 }, (_, i) => ({ value: i * step, y: y(i * step) }))
  const xTickCount = innerWidth < 220 ? 3 : 4
  const tickFormat = last - first > 300 * DAY ? monthYear : shortDate
  const xTicks = Array.from({ length: xTickCount }, (_, i) => {
    const time = first + ((last - first) * i) / (xTickCount - 1)
    return { label: tickFormat.format(new Date(time)), x: x(time), anchor: i === 0 ? 'start' : i === xTickCount - 1 ? 'end' : 'middle' }
  })

  return { lines, yTicks, xTicks, baseline, innerWidth, x, y, first, last, endX: x(last) }
})

function onPointerMove(event: PointerEvent) {
  const svg = event.currentTarget as SVGSVGElement
  const offsetX = event.clientX - svg.getBoundingClientRect().left
  const { first, last, innerWidth } = chart.value
  const time = first + ((offsetX - MARGIN.left) / innerWidth) * (last - first)
  hoverTime.value = Math.min(Math.max(time, first), last)
}

const hovered = computed(() => {
  if (hoverTime.value === null) return null
  const time = hoverTime.value
  const x = chart.value.x(time)
  const rows = chart.value.lines
    .map((line) => ({ id: line.id, name: line.name, color: line.color, opacity: line.opacity, value: valueAt(line.points, time) }))
    .sort((a, b) => b.value - a.value)
  const left = Math.min(Math.max(x, 90), width.value - 90)
  return { time, x, rows, left }
})

const ariaLabel = computed(() =>
  chart.value.lines.map((line) => `${line.name} : ${numberFormat.format(line.endValue)} points`).join(', '),
)
</script>

<template>
  <div ref="container" class="progress-chart">
    <ul class="progress-chart__legend">
      <li v-for="line in legend" :key="line.id">
        <span class="progress-chart__swatch" :style="{ background: line.color, opacity: line.opacity }" />
        {{ line.name }}<template v-if="line.isMe"> (vous)</template>
      </li>
    </ul>

    <svg
      :width="width"
      :height="HEIGHT"
      role="img"
      :aria-label="`Score cumulé — ${ariaLabel}`"
      @pointermove="onPointerMove"
      @pointerleave="hoverTime = null"
    >
      <g class="progress-chart__grid">
        <line v-for="tick in chart.yTicks" :key="tick.value" :x1="MARGIN.left" :x2="chart.endX" :y1="tick.y" :y2="tick.y" />
      </g>
      <g class="progress-chart__axis">
        <text v-for="tick in chart.yTicks" :key="tick.value" :x="MARGIN.left - 8" :y="tick.y" text-anchor="end" dominant-baseline="middle">
          {{ numberFormat.format(tick.value) }}
        </text>
        <text v-for="tick in chart.xTicks" :key="tick.label + tick.x" :x="tick.x" :y="HEIGHT - 6" :text-anchor="tick.anchor">
          {{ tick.label }}
        </text>
      </g>
      <path
        v-for="line in chart.lines"
        :key="line.id"
        :d="line.path"
        class="progress-chart__line"
        :style="{ stroke: line.color, strokeOpacity: line.opacity }"
      />
      <!-- End markers with a surface ring. -->
      <circle
        v-for="line in chart.lines"
        :key="`end-${line.id}`"
        :cx="chart.endX"
        :cy="line.endY"
        r="4"
        class="progress-chart__dot"
        :style="{ fill: line.color, fillOpacity: line.opacity }"
      />
      <template v-if="hovered">
        <line :x1="hovered.x" :x2="hovered.x" :y1="MARGIN.top" :y2="chart.baseline" class="progress-chart__crosshair" />
        <circle
          v-for="line in chart.lines"
          :key="`hover-${line.id}`"
          :cx="hovered.x"
          :cy="chart.y(valueAt(line.points, hovered.time))"
          r="4"
          class="progress-chart__dot"
          :style="{ fill: line.color, fillOpacity: line.opacity }"
        />
      </template>
    </svg>

    <div v-if="hovered" class="progress-chart__tooltip" :style="{ left: `${hovered.left}px` }">
      <strong>{{ formatDate(localDate(hovered.time)) }}</strong>
      <span v-for="row in hovered.rows" :key="row.id" class="progress-chart__row">
        <span class="progress-chart__swatch" :style="{ background: row.color, opacity: row.opacity }" />
        <span>{{ row.name }}</span>
        <span class="progress-chart__value">{{ numberFormat.format(row.value) }} pts</span>
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

.progress-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  margin: 0 0 8px;
  padding: 0;
  list-style: none;
  font-size: 0.85rem;
}

.progress-chart__legend li {
  display: flex;
  align-items: center;
  gap: 6px;
}

.progress-chart__swatch {
  flex-shrink: 0;
  width: 12px;
  height: 3px;
  border-radius: 2px;
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

.progress-chart__line {
  fill: none;
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.progress-chart__dot {
  stroke: var(--surface);
  stroke-width: 2;
}

.progress-chart__crosshair {
  stroke: var(--muted);
  stroke-width: 1;
}

.progress-chart__tooltip {
  position: absolute;
  top: 28px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-2);
  box-shadow: var(--shadow);
  font-size: 0.8rem;
  white-space: nowrap;
  pointer-events: none;
}

.progress-chart__row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.progress-chart__value {
  margin-left: auto;
  padding-left: 12px;
  font-variant-numeric: tabular-nums;
}
</style>
