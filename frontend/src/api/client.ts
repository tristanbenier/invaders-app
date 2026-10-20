export type FieldErrors = Record<string, string[]>

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(firstMessage(data) ?? `Erreur ${status}`)
  }

  /** Field errors as returned by DRF ("non_field_errors" and "detail" go to "_"). */
  get fields(): FieldErrors {
    const errors: FieldErrors = {}
    if (typeof this.data === 'string') {
      errors._ = [this.data]
    } else if (Array.isArray(this.data)) {
      errors._ = this.data.map(String)
    } else if (this.data && typeof this.data === 'object') {
      for (const [key, value] of Object.entries(this.data)) {
        const target = key === 'non_field_errors' || key === 'detail' ? '_' : key
        errors[target] = [...(errors[target] ?? []), ...(Array.isArray(value) ? value.map(String) : [String(value)])]
      }
    }
    return errors
  }
}

function firstMessage(data: unknown): string | undefined {
  if (typeof data === 'string') return data
  if (Array.isArray(data)) return data.length ? firstMessage(data[0]) : undefined
  if (data && typeof data === 'object') {
    for (const value of Object.values(data)) {
      const message = firstMessage(value)
      if (message) return message
    }
  }
  return undefined
}

function getCookie(name: string): string | undefined {
  return document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')[1]
}

async function ensureCsrfCookie() {
  if (!getCookie('csrftoken')) {
    await fetch('/api/auth/csrf/', { credentials: 'same-origin' })
  }
}

type Query = Record<string, string | number | boolean | null | undefined>

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: unknown
  query?: Query
}

export async function api<T>(path: string, { method = 'GET', body, query }: RequestOptions = {}): Promise<T> {
  const url = new URL(`/api${path}`, window.location.origin)
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== null && value !== undefined && value !== '') url.searchParams.set(key, String(value))
  }

  const headers: Record<string, string> = { Accept: 'application/json' }
  let payload: BodyInit | undefined
  if (method !== 'GET') {
    await ensureCsrfCookie()
    headers['X-CSRFToken'] = getCookie('csrftoken') ?? ''
  }
  if (body instanceof FormData) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(url, { method, headers, body: payload, credentials: 'same-origin' })
  } catch {
    throw new ApiError(0, 'Impossible de joindre le serveur. Vérifiez votre connexion.')
  }
  if (response.status === 204) return undefined as T
  const data = response.headers.get('Content-Type')?.includes('application/json') ? await response.json() : null
  if (!response.ok) throw new ApiError(response.status, data ?? `Erreur ${response.status}`)
  return data as T
}
