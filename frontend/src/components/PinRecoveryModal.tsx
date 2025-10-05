import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'
import { usersApi } from '@/api/client'
import type { User } from '@/api/types'

interface PinRecoveryModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
  user: User | null
}

const PinRecoveryModal: React.FC<PinRecoveryModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  user,
}) => {
  const { t } = useTranslation()
  const [currentPin, setCurrentPin] = useState('')
  const [newPin, setNewPin] = useState('')
  const [confirmPin, setConfirmPin] = useState('')
  const [error, setError] = useState('')

  const recoverPinMutation = useMutation({
    mutationFn: ({ currentPin, newPin }: { currentPin: string; newPin: string }) => {
      if (!user) throw new Error('No user selected')
      return usersApi.recoverPin(user.id, newPin, 'current_pin', currentPin)
    },
    onSuccess: () => {
      setCurrentPin('')
      setNewPin('')
      setConfirmPin('')
      setError('')
      onSuccess?.()
      onClose()
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || t('pin.recoveryError'))
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!currentPin.trim()) {
      setError(t('pin.currentPinRequired'))
      return
    }

    if (!newPin.trim()) {
      setError(t('pin.newPinRequired'))
      return
    }

    if (newPin !== confirmPin) {
      setError(t('pin.pinMismatch'))
      return
    }

    if (newPin.length < 4) {
      setError(t('pin.tooShort'))
      return
    }

    recoverPinMutation.mutate({ currentPin, newPin })
  }

  const handleClose = () => {
    setCurrentPin('')
    setNewPin('')
    setConfirmPin('')
    setError('')
    onClose()
  }

  if (!isOpen || !user) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4">
          {t('pin.recoverPinTitle', { name: user.display_name })}
        </h3>
        
        <p className="text-gray-600 text-sm mb-4">
          {t('pin.recoverPinDescription')}
        </p>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="currentPin" className="block text-sm font-medium text-gray-700 mb-2">
                {t('pin.currentPin')}
              </label>
              <input
                type="password"
                id="currentPin"
                value={currentPin}
                onChange={(e) => setCurrentPin(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('pin.placeholder')}
                disabled={recoverPinMutation.isPending}
                autoFocus
              />
            </div>
            
            <div>
              <label htmlFor="newPin" className="block text-sm font-medium text-gray-700 mb-2">
                {t('pin.newPin')}
              </label>
              <input
                type="password"
                id="newPin"
                value={newPin}
                onChange={(e) => setNewPin(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('pin.newPinPlaceholder')}
                disabled={recoverPinMutation.isPending}
              />
            </div>
            
            <div>
              <label htmlFor="confirmPin" className="block text-sm font-medium text-gray-700 mb-2">
                {t('pin.confirmPin')}
              </label>
              <input
                type="password"
                id="confirmPin"
                value={confirmPin}
                onChange={(e) => setConfirmPin(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('pin.confirmPinPlaceholder')}
                disabled={recoverPinMutation.isPending}
              />
            </div>
            
            {error && (
              <p className="text-red-500 text-sm">{error}</p>
            )}
          </div>
          
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={handleClose}
              disabled={recoverPinMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={recoverPinMutation.isPending || !currentPin.trim() || !newPin.trim() || !confirmPin.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {recoverPinMutation.isPending ? t('common.loading') : t('pin.recoverPin')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PinRecoveryModal