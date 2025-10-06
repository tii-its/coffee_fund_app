import React, { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { usersApi } from '@/api/client'
import type { User } from '@/api/types'

interface UserPinConfirmModalProps {
  user: User | null
  isOpen: boolean
  onSuccess: (user: User) => void
  onCancel: () => void
  autoFocus?: boolean
  show: boolean
}

const UserPinConfirmModal: React.FC<UserPinConfirmModalProps> = ({ user, isOpen, onSuccess, onCancel, autoFocus = true, show }) => {
  const { t } = useTranslation()
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isOpen) {
      setPin('')
      setError('')
    }
  }, [isOpen])

  const verifyMutation = useMutation({
    mutationFn: () => {
      if (!user) throw new Error('No user')
      return usersApi.verifyPin(user.id, pin)
    },
    onSuccess: () => {
      setError('')
      onSuccess(user as User)
      setPin('')
    },
    onError: (err: unknown) => {
      // Attempt to extract backend detail
      const detail = (err as any)?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : t('pin.invalid'))
    },
  })

  if (!isOpen || !show || !user) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-sm shadow-lg">
        <h3 className="text-lg font-semibold mb-2">{t('pin.confirmAccessTitle', { name: user.display_name })}</h3>
        <p className="text-sm text-gray-600 mb-4">{t('pin.confirmAccessMessage')}</p>
  <form onSubmit={(e: React.FormEvent) => { e.preventDefault(); verifyMutation.mutate(); }}>
          <input
            type="password"
            className="w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={t('pin.placeholder')}
            value={pin}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPin(e.target.value)}
            disabled={verifyMutation.isPending}
            autoFocus={autoFocus}
          />
          {error && <div className="text-xs text-red-600 mb-2">{error}</div>}
          <div className="flex justify-end space-x-3 mt-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-3 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300"
              disabled={verifyMutation.isPending}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={!pin.trim() || verifyMutation.isPending}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {verifyMutation.isPending ? t('common.loading') : t('pin.confirmAccess')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default UserPinConfirmModal
