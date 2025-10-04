import { useEffect } from 'react'
import { useAppStore } from '@/store'

// Hook to automatically clear actor after timeout
export function useActorExpiry() {
  const { actorAuthenticatedAt, actorTimeoutMinutes = 10, clearActor, actorId } = useAppStore()

  useEffect(() => {
    if (!actorId || !actorAuthenticatedAt) return
    const timeoutMs = actorTimeoutMinutes * 60 * 1000
    const expiresAt = actorAuthenticatedAt + timeoutMs
    const remaining = expiresAt - Date.now()
    if (remaining <= 0) {
      clearActor()
      return
    }
    const timer = setTimeout(() => {
      clearActor()
    }, remaining)
    return () => clearTimeout(timer)
  }, [actorAuthenticatedAt, actorTimeoutMinutes, clearActor, actorId])
}
