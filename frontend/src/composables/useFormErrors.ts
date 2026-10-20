import { ref } from 'vue'

import { ApiError, type FieldErrors } from '@/api/client'

/** Collects API field errors; "_" holds global errors. */
export function useFormErrors() {
  const errors = ref<FieldErrors>({})

  function capture(error: unknown) {
    errors.value = error instanceof ApiError ? error.fields : { _: [String(error)] }
  }

  function clear() {
    errors.value = {}
  }

  return { errors, capture, clear }
}
