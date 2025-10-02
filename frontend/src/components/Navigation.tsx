import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Navigation() {
  const { user, logout } = useAuth()

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold">
              🚴 Vélivert Analytics
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              to="/"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Dashboard
            </Link>
            <Link
              to="/stations"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Stations
            </Link>
            <Link
              to="/bikes"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Vélos
            </Link>
            <Link
              to="/bike-flows"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Flux
            </Link>
            <Link
              to="/interventions"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Interventions
            </Link>
            <Link
              to="/analytics"
              className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
            >
              Analytics
            </Link>
            {user?.role === 'admin' && (
              <Link
                to="/admin"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition"
              >
                Administration
              </Link>
            )}

            {/* User info and logout */}
            <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-blue-500">
              <div className="text-sm">
                <div className="font-medium">{user?.full_name}</div>
                <div className="text-xs text-blue-200">{user?.role}</div>
              </div>
              <button
                onClick={logout}
                className="px-3 py-2 rounded-md text-sm font-medium bg-blue-700 hover:bg-blue-800 transition"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}