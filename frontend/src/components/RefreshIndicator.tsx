import { useEffect, useState } from 'react'

interface RefreshIndicatorProps {
  isRefreshing: boolean
  lastRefresh?: Date
}

export default function RefreshIndicator({ isRefreshing, lastRefresh }: RefreshIndicatorProps) {
  const [showNotification, setShowNotification] = useState(false)

  useEffect(() => {
    if (isRefreshing) {
      setShowNotification(true)
    } else if (showNotification) {
      // Hide notification after 2 seconds once refresh is complete
      const timer = setTimeout(() => {
        setShowNotification(false)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [isRefreshing, showNotification])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <>
      {/* Floating notification */}
      {showNotification && (
        <div className="fixed top-20 right-4 z-50 animate-fade-in-down">
          <div className={`rounded-lg shadow-lg px-4 py-3 flex items-center gap-3 ${
            isRefreshing
              ? 'bg-blue-50 border border-blue-200'
              : 'bg-green-50 border border-green-200'
          }`}>
            {isRefreshing ? (
              <>
                <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-sm font-medium text-blue-900">Actualisation des données...</span>
              </>
            ) : (
              <>
                <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm font-medium text-green-900">Données actualisées</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Static indicator in corner */}
      <div className="fixed bottom-4 right-4 z-40">
        <div className="bg-white rounded-lg shadow-md px-3 py-2 text-xs text-gray-600 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isRefreshing ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'}`}></div>
          <span>
            {isRefreshing ? 'Actualisation...' : lastRefresh ? `Mis à jour: ${formatTime(lastRefresh)}` : 'En attente'}
          </span>
        </div>
      </div>
    </>
  )
}
