export type Role = 'admin' | 'member'
export type Status = 'ok' | 'degraded' | 'destroyed' | 'hidden' | 'unknown'
export type MapTheme = 'light' | 'dark'

export const STATUS_LABELS: Record<Status, string> = {
  ok: 'Intact',
  degraded: 'Dégradé',
  destroyed: 'Détruit',
  hidden: 'Caché',
  unknown: 'Inconnu',
}

export interface TeamSummary {
  id: number
  name: string
}

export interface Me {
  id: number
  email: string
  display_name: string
  role: Role
  team: TeamSummary
  map_theme: MapTheme
  /** A Flash Invaders UID is saved (the UID itself is never sent back). */
  flash_sync_enabled: boolean
  /** Keep the manual flash buttons even with the sync on. */
  manual_flash: boolean
}

export interface Member {
  id: number
  display_name: string
  role: Role
  date_joined: string
}

export interface Team extends TeamSummary {
  created_at: string
  members: Member[]
}

export interface UserSummary {
  id: number
  display_name: string
}

export interface Invitation {
  id: number
  email: string
  invited_by: Member | null
  url: string
  created_at: string
  expires_at: string
}

export interface PublicInvitation {
  team: TeamSummary
  invited_by: string | null
  email: string
  expires_at: string
}

export interface Country {
  id: number
  name: string
}

export interface City {
  id: number
  name: string
  prefix: string
  country: number
  image: string | null
}

export interface Invader {
  id: number
  name: string
  city: number
  lat: number
  lng: number
  points: number
  status: Status
  image: string | null
  address1: string
  address2: string
  zip: string
  comment: string
  created_by: UserSummary | null
  created_at: string
  updated_at: string
  my_flashed_at: string | null
  flash_count: number
}

export interface Flasher {
  user: UserSummary
  flashed_at: string
}

export interface InvaderDetail extends Invader {
  flashers: Flasher[]
}

export type HistoryAction = 'created' | 'updated' | 'imported'

export interface HistoryChange<T = unknown> {
  old: T
  new: T
}

export interface HistoryEntry {
  id: number
  user: UserSummary | null
  action: HistoryAction
  changes: Partial<
    Record<'name' | 'lat' | 'lng' | 'points' | 'status' | 'image' | 'address1' | 'address2' | 'zip' | 'comment', HistoryChange>
  >
  created_at: string
}

export interface CityProgress {
  city: { id: number; name: string; prefix: string }
  country: string
  total: number
  flashed: number
}

export interface PointsProgress {
  points: number
  total: number
  flashed: number
}

export interface TimelinePoint {
  date: string
  points: number
  flashes: number
  cumulative_points: number
  cumulative_flashes: number
}

export interface MyStats {
  points: number
  /** `points` is the Flash Invaders app's score (synced account), not the sum of the flashes here. */
  points_from_app: boolean
  flashes: number
  cities: number
  team_invaders: number
  team_cities: number
  timeline: TimelinePoint[]
  by_city: CityProgress[]
  by_points: PointsProgress[]
}

export interface MemberTimeline {
  user: UserSummary
  /** Cumulative points and flashes of the member on each of their flash days (team invaders only). */
  points: { date: string; cumulative_points: number; cumulative_flashes: number }[]
}

export interface TeamStats {
  invaders: number
  timelines: MemberTimeline[]
  /** `points_from_app`: Flash Invaders score of a synced member, else the sum of their flashes here. */
  ranking: { user: UserSummary; points: number; points_from_app: boolean; flashes: number }[]
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type TransportMode = 'walk' | 'bike' | 'car' | 'transit'

export const TRANSPORT_LABELS: Record<TransportMode, string> = {
  walk: 'À pied',
  bike: 'À vélo',
  car: 'En voiture',
  transit: 'En transports',
}

export interface OutingStop {
  position: number
  invader: { id: number; name: string; lat: number; lng: number; points: number; status: Status }
  /** Every participant has flashed it. */
  done: boolean
}

export interface Outing {
  id: number
  name: string
  created_by: UserSummary | null
  participants: number[]
  participant_names: UserSummary[]
  city: number | null
  mode: TransportMode
  duration_minutes: number
  start_lat: number
  start_lng: number
  start_label: string
  is_loop: boolean
  end_lat: number
  end_lng: number
  end_label: string
  stops: OutingStop[]
  /** As the crow flies + 30% for the streets, flashes included. */
  estimate: { distance_km: number; minutes: number }
  created_at: string
  updated_at: string
}

export type OutingInput = Pick<
  Outing,
  'name' | 'participants' | 'city' | 'mode' | 'duration_minutes' | 'start_lat' | 'start_lng' | 'start_label' | 'is_loop'
> &
  Partial<Pick<Outing, 'end_lat' | 'end_lng' | 'end_label'>>
