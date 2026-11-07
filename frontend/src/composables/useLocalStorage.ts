import { ref, watch, type Ref } from 'vue'

/**
 * Ref kept in localStorage as JSON (per browser, nothing to sync).
 * Falls back to `defaultValue` when the stored value is missing, corrupted or rejected
 * by `isValid`; when storage is blocked (private mode), the value lasts until reload.
 */
export function useLocalStorage<T>(key: string, defaultValue: T, isValid?: (value: unknown) => value is T): Ref<T> {
  const value = ref(read()) as Ref<T>

  function read(): T {
    try {
      const raw = localStorage.getItem(key)
      if (raw !== null) {
        const parsed: unknown = JSON.parse(raw)
        if (!isValid || isValid(parsed)) return parsed as T
      }
    } catch {
      // Storage blocked or corrupted value: use the default.
    }
    return defaultValue
  }

  watch(
    value,
    (current) => {
      try {
        localStorage.setItem(key, JSON.stringify(current))
      } catch {
        // Storage unavailable: the value is simply not remembered.
      }
    },
    { deep: true },
  )

  return value
}
