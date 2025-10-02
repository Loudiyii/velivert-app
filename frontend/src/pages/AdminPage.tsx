import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../services/api'
import axios from 'axios'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
}

export default function AdminPage() {
  const { user } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'technician'
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Check if user is admin
  if (user?.role !== 'admin') {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-red-600 mb-4">Accès Refusé</h1>
        <p className="text-gray-600">Vous devez être administrateur pour accéder à cette page.</p>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      await authApi.register(formData)
      setSuccess(`Utilisateur ${formData.email} créé avec succès!`)
      setFormData({
        email: '',
        password: '',
        full_name: '',
        role: 'technician'
      })
      setShowForm(false)
      // Refresh users list if we had one
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création de l\'utilisateur')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Administration</h1>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {success}
        </div>
      )}

      {/* User Management Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-700">Gestion des Utilisateurs</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            {showForm ? 'Annuler' : '+ Créer Utilisateur'}
          </button>
        </div>

        {/* Create User Form */}
        {showForm && (
          <div className="border-t pt-4">
            <h3 className="text-lg font-medium text-gray-700 mb-4">Créer un Nouveau Utilisateur</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom Complet
                  </label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                    placeholder="Jean Dupont"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                    placeholder="email@exemple.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mot de Passe
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                    placeholder="••••••••"
                    required
                    minLength={6}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rôle
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                  >
                    <option value="viewer">Viewer (Lecture seule)</option>
                    <option value="technician">Technician (Interventions)</option>
                    <option value="admin">Admin (Accès complet)</option>
                  </select>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
                >
                  {loading ? 'Création...' : 'Créer l\'utilisateur'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Info about user management */}
        {!showForm && (
          <div className="text-gray-600">
            <p>Utilisez ce panneau pour créer des comptes pour les techniciens et autres utilisateurs.</p>
            <div className="mt-4 space-y-2">
              <p className="text-sm"><strong>Viewer:</strong> Peut voir les données (lecture seule)</p>
              <p className="text-sm"><strong>Technician:</strong> Peut créer et gérer des interventions</p>
              <p className="text-sm"><strong>Admin:</strong> Accès complet, peut créer des utilisateurs</p>
            </div>
          </div>
        )}
      </div>

      {/* System Info */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Informations Système</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-600 mb-1">Stations</h3>
            <p className="text-2xl font-bold text-blue-600">5</p>
            <p className="text-xs text-gray-500">actives</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-600 mb-1">Vélos</h3>
            <p className="text-2xl font-bold text-green-600">50</p>
            <p className="text-xs text-gray-500">en circulation</p>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-600 mb-1">Interventions</h3>
            <p className="text-2xl font-bold text-orange-600">20</p>
            <p className="text-xs text-gray-500">en cours</p>
          </div>
        </div>
      </div>
    </div>
  )
}
