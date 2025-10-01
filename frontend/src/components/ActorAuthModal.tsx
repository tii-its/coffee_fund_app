// NOTE: Deprecated. Per-action PIN entry now used; this modal retained only for potential future UX improvements.
import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '@/store'
import { usersApi } from '@/api/client'
import type { User } from '@/api/types'

interface ActorAuthModalProps {
  isOpen: boolean
  onClose: () => void
  requiredRole?: 'treasurer' | 'admin' | 'treasurer-or-admin'
  timeoutMinutes?: number
  onAuthenticated?: () => void
}

const ActorAuthModal: React.FC<ActorAuthModalProps> = ({
  isOpen,
  onClose,
  requiredRole = 'treasurer',
  timeoutMinutes = 10,
  onAuthenticated,
}) => {
  const { t } = useTranslation()
  const { setActor, actorId, actorRole, actorPin, clearActor } = useAppStore()
  const [users, setUsers] = useState<User[]>([])
  const [selectedActorId, setSelectedActorId] = useState<string>('')
  const [pin, setPin] = useState('')
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    // fetch active treasurers/admins
    usersApi.getAll({ active_only: true }).then(res => {
      const filtered = res.data.filter(u => u.role === 'treasurer' || u.role === 'admin')
      setUsers(filtered)
    }).catch(err => {
      console.error('Failed to load users for actor auth', err)
    })
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) {
      setSelectedActorId('')
      setPin('')
      setError('')
    }
  }, [isOpen])

  if (!isOpen) return null

  const meetsRoleRequirement = (role: string) => {
    if (requiredRole === 'treasurer-or-admin') return role === 'treasurer' || role === 'admin'
    return role === requiredRole
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!selectedActorId) {
      setError(t('pin.actorRequired'))
      return
    }
    if (!pin.trim()) {
      setError(t('pin.required'))
      return
    }

    const actorUser = users.find(u => u.id === selectedActorId)
    if (!actorUser) {
      setError(t('errors.userNotFound'))
      return
    }
    if (!meetsRoleRequirement(actorUser.role)) {
      setError(t('errors.forbidden'))
      return
    }

    try {
      setLoading(true)
      // Light verification call: fetch balances (treasurer) or users list (admin) to force backend auth
      if (actorUser.role === 'treasurer') {
        await usersApi.getAllBalances()
      } else if (actorUser.role === 'admin') {
        await usersApi.getAll()
      }
      setActor({ id: actorUser.id, role: actorUser.role as any, pin })
      if (onAuthenticated) onAuthenticated()
      onClose()
    } catch (err: any) {
      console.error('Actor auth failed', err)
      setError(err.response?.data?.detail || t('common.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          🔐 {t('pin.enterActorPin')}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('pin.selectActor')}
            </label>
            <select
              value={selectedActorId}
              onChange={(e) => setSelectedActorId(e.target.value)}
              className="w-full border rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              disabled={loading}
            >
              <option value="">-- {t('common.select')} --</option>
              {users.map(u => (
                <option key={u.id} value={u.id}>
                  {u.display_name} ({u.role})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('pin.pin')}
            </label>
            <input
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="w-full border rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="••••"
              disabled={loading}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            {actorId && (
              <button
                type="button"
                onClick={() => clearActor()}
                className="px-4 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
                disabled={loading}
              >
                {t('pin.clear')}
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
              disabled={loading}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
              disabled={loading}
            >
              {loading ? t('common.loading') : t('common.confirm')}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {t('pin.timeoutInfo', { minutes: timeoutMinutes })}
          </p>
        </form>
      </div>
    </div>
  )
}

export default ActorAuthModal
