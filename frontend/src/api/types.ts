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

export interface TimelinePoint {
  date: string
  points: number
  flashes: number
  cumulative_points: number
  cumulative_flashes: number
}

export interface MyStats {
  points: number
  flashes: number
  cities: number
  team_invaders: number
  timeline: TimelinePoint[]
  by_city: CityProgress[]
}

export interface TeamStats {
  invaders: number
  ranking: { user: UserSummary; points: number; flashes: number }[]
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
