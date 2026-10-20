const dateFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

export function formatDate(value: string) {
  // Plain dates ("2026-10-19") are local dates, not UTC midnight.
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value)
  return dateFormat.format(date)
}

export function today() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60_000
  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}
