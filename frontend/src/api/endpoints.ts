import { api } from './client'
import type {
  City,
  Country,
  Invader,
  InvaderDetail,
  Invitation,
  MapTheme,
  Me,
  MyStats,
  Outing,
  OutingInput,
  Paginated,
  PublicInvitation,
  Team,
  TeamStats,
} from './types'

export interface InvaderFilters {
  search?: string
  city?: number | null
  country?: number | null
  status?: string
  points?: string
  flashed?: 'true' | 'false'
  /** Comma-separated member ids: flashed by all of them / by none of them. */
  flashed_by?: string
  not_flashed_by?: string
  ordering?: string
}

export const authApi = {
  me: () => api<Me>('/auth/me/'),
  flashInvadersUid: () => api<{ uid: string }>('/auth/me/flash-invaders-uid/'),
  updateMe: (body: { map_theme?: MapTheme; flash_invaders_uid?: string; manual_flash?: boolean }) =>
    api<Me>('/auth/me/', { method: 'PATCH', body }),
  login: (email: string, password: string) => api<Me>('/auth/login/', { method: 'POST', body: { email, password } }),
  logout: () => api<void>('/auth/logout/', { method: 'POST' }),
  invitation: (token: string) => api<PublicInvitation>(`/auth/invitations/${token}/`),
  acceptInvitation: (body: { token: string; email: string; display_name: string; password: string }) =>
    api<Me>('/auth/accept-invitation/', { method: 'POST', body }),
}

export const teamApi = {
  get: () => api<Team>('/team/'),
  removeMember: (id: number) => api<void>(`/team/members/${id}/`, { method: 'DELETE' }),
  invitations: () => api<Invitation[]>('/invitations/'),
  invite: (email = '') => api<Invitation>('/invitations/', { method: 'POST', body: { email } }),
  revokeInvitation: (id: number) => api<void>(`/invitations/${id}/`, { method: 'DELETE' }),
}

export const outingsApi = {
  list: () => api<Outing[]>('/outings/'),
  get: (id: number) => api<Outing>(`/outings/${id}/`),
  create: (body: OutingInput) => api<Outing>('/outings/', { method: 'POST', body }),
  update: (id: number, body: Partial<OutingInput> & { stop_ids?: number[] }) =>
    api<Outing>(`/outings/${id}/`, { method: 'PATCH', body }),
  remove: (id: number) => api<void>(`/outings/${id}/`, { method: 'DELETE' }),
  /** Recompute the whole route from the outing's settings. */
  plan: (id: number) => api<Outing>(`/outings/${id}/plan/`, { method: 'POST' }),
  /** Shortest order for the current invaders. */
  optimize: (id: number) => api<Outing>(`/outings/${id}/optimize/`, { method: 'POST' }),
}

export const placesApi = {
  countries: () => api<Country[]>('/countries/'),
  cities: () => api<City[]>('/cities/'),
  createCity: (body: { name: string; prefix: string; country?: number; country_name?: string }) =>
    api<City>('/cities/', { method: 'POST', body }),
  updateCity: (id: number, body: { country?: number; country_name?: string }) =>
    api<City>(`/cities/${id}/`, { method: 'PATCH', body }),
}

export const invadersApi = {
  list: (filters: InvaderFilters = {}) => api<Invader[]>('/invaders/', { query: { ...filters } }),
  page: (filters: InvaderFilters, page: number, page_size = 30) =>
    api<Paginated<Invader>>('/invaders/', { query: { ...filters, page, page_size } }),
  search: (search: string) =>
    api<Paginated<Invader>>('/invaders/', { query: { search, page: 1, page_size: 8 } }),
  get: (id: number) => api<InvaderDetail>(`/invaders/${id}/`),
  create: (body: FormData) => api<Invader>('/invaders/', { method: 'POST', body }),
  update: (id: number, body: FormData | Partial<Invader>) =>
    api<Invader>(`/invaders/${id}/`, { method: 'PATCH', body }),
  remove: (id: number) => api<void>(`/invaders/${id}/`, { method: 'DELETE' }),
  flash: (id: number, flashed_at?: string) =>
    api<InvaderDetail>(`/invaders/${id}/flash/`, { method: 'POST', body: flashed_at ? { flashed_at } : {} }),
  unflash: (id: number) => api<InvaderDetail>(`/invaders/${id}/flash/`, { method: 'DELETE' }),
  /** Flashes the team invaders flashed in the Flash Invaders app; `full` skips the count shortcut. */
  syncFlashes: (full: boolean) =>
    api<{ created: string[]; updated: number }>('/flashes/sync/', { method: 'POST', query: full ? { full: 1 } : {} }),
}

export const statsApi = {
  me: () => api<MyStats>('/stats/me/'),
  team: () => api<TeamStats>('/stats/team/'),
}

export interface PlaceResult {
  label: string
  lat: number
  lng: number
}

export const geocodeApi = {
  reverse: (lat: number, lng: number) =>
    api<{ address1: string; zip: string; city: string }>('/geocode/reverse/', { query: { lat, lng } }),
  search: (q: string, near?: { lat: number; lng: number }) =>
    api<PlaceResult[]>('/geocode/search/', { query: { q, lat: near?.lat, lng: near?.lng } }),
}

export interface IssPosition {
  lat: number
  lng: number
  altitude_km: number
  velocity_kmh: number
  timestamp: number
}

export const issApi = {
  position: () => api<IssPosition>('/iss/'),
}
