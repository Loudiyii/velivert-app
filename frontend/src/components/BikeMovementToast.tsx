import { useEffect, useState } from 'react'

interface BikeMovement {
  id: string
  bike_id: string
  from_station_id: string | null
  to_station_id: string | null
  movement_type: string
  detected_at: string
}

interface BikeMovementToastProps {
  movements: BikeMovement[]
}

interface ToastNotification {
  id: string
  message: string
  type: 'pickup' | 'dropoff' | 'relocation' | 'in_transit'
  timestamp: Date
}

export default function BikeMovementToast({ movements }: BikeMovementToastProps) {
  const [notifications, setNotifications] = useState<ToastNotification[]>([])
  const [lastMovementCount, setLastMovementCount] = useState(0)

  useEffect(() => {
    // Détecte les nouveaux mouvements
    if (movements.length > lastMovementCount && lastMovementCount > 0) {
      const newMovements = movements.slice(0, movements.length - lastMovementCount)

      newMovements.forEach((movement) => {
        const bikeIdShort = movement.bike_id.substring(0, 8)
        let message = ''
        let type: 'pickup' | 'dropoff' | 'relocation' | 'in_transit' = 'in_transit'

        switch (movement.movement_type) {
          case 'pickup':
            message = `🚴 Vélo ${bikeIdShort} récupéré${movement.from_station_id ? ' d\'une station' : ''}`
            type = 'pickup'
            break
          case 'dropoff':
            message = `📍 Vélo ${bikeIdShort} déposé${movement.to_station_id ? ' à une station' : ''}`
            type = 'dropoff'
            break
          case 'relocation':
            message = `🔄 Vélo ${bikeIdShort} relocalisé entre stations`
            type = 'relocation'
            break
          case 'in_transit':
            message = `🚲 Vélo ${bikeIdShort} en circulation`
            type = 'in_transit'
            break
          default:
            message = `🔔 Vélo ${bikeIdShort} en mouvement`
        }

        const notification: ToastNotification = {
          id: `${movement.id}-${Date.now()}`,
          message,
          type,
          timestamp: new Date()
        }

        setNotifications((prev) => [notification, ...prev].slice(0, 5)) // Garder max 5 notifications
      })
    }

    setLastMovementCount(movements.length)
  }, [movements])

  // Auto-suppression après 8 secondes
  useEffect(() => {
    if (notifications.length > 0) {
      const timer = setTimeout(() => {
        setNotifications((prev) => prev.slice(0, -1))
      }, 8000)

      return () => clearTimeout(timer)
    }
  }, [notifications])

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'pickup':
        return 'bg-blue-500'
      case 'dropoff':
        return 'bg-green-500'
      case 'relocation':
        return 'bg-purple-500'
      case 'in_transit':
        return 'bg-orange-500'
      default:
        return 'bg-gray-500'
    }
  }

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }

  return (
    <div className="fixed top-20 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`${getTypeColor(notification.type)} text-white px-4 py-3 rounded-lg shadow-lg transform transition-all duration-300 animate-slide-in-right flex items-center justify-between`}
          style={{
            animation: 'slideInRight 0.3s ease-out'
          }}
        >
          <div className="flex-1">
            <p className="text-sm font-medium">{notification.message}</p>
            <p className="text-xs opacity-80 mt-1">
              {notification.timestamp.toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={() => removeNotification(notification.id)}
            className="ml-3 text-white hover:text-gray-200 focus:outline-none"
          >
            ✕
          </button>
        </div>
      ))}

      <style>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        .animate-slide-in-right {
          animation: slideInRight 0.3s ease-out;
        }
      `}</style>
    </div>
  )
}
