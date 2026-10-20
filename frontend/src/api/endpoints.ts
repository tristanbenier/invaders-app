import { api } from './client'
import type {
  City,
  HistoryEntry,
  Country,
  Invader,
  InvaderDetail,
  Invitation,
  MapTheme,
  Me,
  MyStats,
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
  flashed?: 'true' | 'false'
  flashed_by?: number | null
  not_flashed_by?: number | null
  ordering?: string
}

export const authApi = {
  me: () => api<Me>('/auth/me/'),
  updateMe: (body: { map_theme: MapTheme }) => api<Me>('/auth/me/', { method: 'PATCH', body }),
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

export const placesApi = {
  countries: () => api<Country[]>('/countries/'),
  cities: () => api<City[]>('/cities/'),
  createCity: (body: { name: string; prefix: string; country?: number; country_name?: string }) =>
    api<City>('/cities/', { method: 'POST', body }),
}

export const invadersApi = {
  list: (filters: InvaderFilters = {}) => api<Invader[]>('/invaders/', { query: { ...filters } }),
  page: (filters: InvaderFilters, page: number, page_size = 30) =>
    api<Paginated<Invader>>('/invaders/', { query: { ...filters, page, page_size } }),
  search: (search: string) =>
    api<Paginated<Invader>>('/invaders/', { query: { search, page: 1, page_size: 8 } }),
  get: (id: number) => api<InvaderDetail>(`/invaders/${id}/`),
  history: (id: number) => api<HistoryEntry[]>(`/invaders/${id}/history/`),
  create: (body: FormData) => api<Invader>('/invaders/', { method: 'POST', body }),
  update: (id: number, body: FormData | Partial<Invader>) =>
    api<Invader>(`/invaders/${id}/`, { method: 'PATCH', body }),
  remove: (id: number) => api<void>(`/invaders/${id}/`, { method: 'DELETE' }),
  flash: (id: number, flashed_at?: string) =>
    api<InvaderDetail>(`/invaders/${id}/flash/`, { method: 'POST', body: flashed_at ? { flashed_at } : {} }),
  unflash: (id: number) => api<InvaderDetail>(`/invaders/${id}/flash/`, { method: 'DELETE' }),
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
