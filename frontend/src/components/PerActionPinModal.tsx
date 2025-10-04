import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usersApi } from '@/api/client'
import type { User } from '@/api/types'

interface PerActionPinModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (actorId: string, pin: string) => void
  title?: string
  requiredRole?: 'treasurer' | 'admin' | 'treasurer-or-admin'
}

// Lightweight per-action modal: fetch treasurer/admin list lazily when opened.
const PerActionPinModal: React.FC<PerActionPinModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  requiredRole = 'treasurer-or-admin'
}) => {
  const { t } = useTranslation()
  const [users, setUsers] = useState<User[]>([])
  const [loaded, setLoaded] = useState(false)
  const [actorId, setActorId] = useState('')
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  React.useEffect(() => {
    if (isOpen && !loaded) {
      usersApi.getAll({ active_only: true }).then(res => {
        setUsers(res.data.filter(u => (requiredRole === 'treasurer-or-admin') ? (u.role === 'treasurer' || u.role === 'admin') : u.role === requiredRole))
        setLoaded(true)
      }).catch(e => console.error('Failed to load users', e))
    }
    if (!isOpen) {
      setActorId(''); setPin(''); setError('')
    }
  }, [isOpen, loaded, requiredRole])

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!actorId || !pin) { setError(t('pin.required')); return }
    setLoading(true)
    try {
      onSubmit(actorId, pin)
      onClose()
    } catch (err: any) {
      setError(err.message || t('common.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-5">
        <h3 className="text-lg font-semibold mb-4">{title || t('pin.enterActorPin')}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('pin.selectActor')}</label>
            <select className="w-full border rounded px-3 py-2" value={actorId} onChange={e => setActorId(e.target.value)} disabled={loading}>
              <option value="">-- {t('common.select')} --</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.display_name} ({u.role})</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('pin.pin')}</label>
            <input type="password" className="w-full border rounded px-3 py-2" value={pin} onChange={e => setPin(e.target.value)} placeholder="••••" disabled={loading} />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200" disabled={loading}>{t('common.cancel')}</button>
            <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60" disabled={loading}>{loading ? t('common.loading') : t('common.confirm')}</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PerActionPinModal
