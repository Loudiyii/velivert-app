import { useEffect, useRef, useState } from 'react'

interface UseDataPollingOptions {
  enabled?: boolean
  intervalMinutes?: number
  onPoll?: () => Promise<void>
}

/**
 * Hook personnalisé pour le polling de données à intervalles réguliers
 *
 * @param options Configuration du polling
 * @param options.enabled Active/désactive le polling (défaut: true)
 * @param options.intervalMinutes Intervalle en minutes (défaut: 3)
 * @param options.onPoll Fonction à appeler à chaque intervalle
 */
export function useDataPolling({
  enabled = true,
  intervalMinutes = 3,
  onPoll
}: UseDataPollingOptions) {
  const [isPolling, setIsPolling] = useState(false)
  const [lastPollTime, setLastPollTime] = useState<Date | null>(null)
  const [nextPollTime, setNextPollTime] = useState<Date | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!enabled || !onPoll) {
      return
    }

    const poll = async () => {
      if (isPolling) return // Éviter les appels simultanés

      try {
        setIsPolling(true)
        await onPoll()
        setLastPollTime(new Date())

        // Calculer le prochain polling
        const next = new Date()
        next.setMinutes(next.getMinutes() + intervalMinutes)
        setNextPollTime(next)
      } catch (error) {
        console.error('Polling error:', error)
      } finally {
        setIsPolling(false)
      }
    }

    // Premier appel immédiat
    poll()

    // Configuration de l'intervalle
    const intervalMs = intervalMinutes * 60 * 1000
    intervalRef.current = setInterval(poll, intervalMs)

    // Nettoyage
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, intervalMinutes, onPoll])

  return {
    isPolling,
    lastPollTime,
    nextPollTime,
    minutesUntilNextPoll: nextPollTime
      ? Math.max(0, Math.floor((nextPollTime.getTime() - Date.now()) / 60000))
      : null
  }
}
