import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'
import { usersApi } from '@/api/client'
import { useAppStore } from '@/store'

interface PinChangeModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

const PinChangeModal: React.FC<PinChangeModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { t } = useTranslation()
  const { currentUser } = useAppStore()
  const [currentPin, setCurrentPin] = useState('')
  const [newPin, setNewPin] = useState('')
  const [confirmPin, setConfirmPin] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const changePinMutation = useMutation({
    mutationFn: ({ currentPin, newPin }: { currentPin: string; newPin: string }) => {
      if (!currentUser?.id) throw new Error(t('pin.noUserSelected'))
      return usersApi.changePin(currentPin, newPin, currentUser.id)
    },
    onSuccess: () => {
      setSuccess(true)
      setError('')
      setTimeout(() => {
        setSuccess(false)
        setCurrentPin('')
        setNewPin('')
        setConfirmPin('')
        onSuccess?.()
        onClose()
      }, 900) // brief confirmation
    },
    onError: (error: any) => {
      // Normalize possible backend error shapes
      const detail = error?.response?.data?.detail
      let message: string
      if (Array.isArray(detail)) {
        // Pydantic validation errors array
        message = detail.map((d: any) => d.msg || d.type || 'validation error').join('; ')
      } else if (typeof detail === 'string') {
        message = detail
      } else if (error.message) {
        message = error.message
      } else {
        message = t('pin.changeError')
      }
      setError(message)
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!currentPin.trim()) {
      setError(t('pin.required'))
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

    changePinMutation.mutate({ currentPin, newPin })
  }

  const handleClose = () => {
    setCurrentPin('')
    setNewPin('')
    setConfirmPin('')
    setError('')
    onClose()
  }

  if (!isOpen) return null

  // Gracefully handle scenario where modal opens without a currentUser context
  if (isOpen && !currentUser) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
          <h3 className="text-lg font-semibold mb-4">{t('pin.change')}</h3>
          <p className="text-sm text-red-600 mb-4">{t('pin.noUserSelectedMessage', 'Select yourself first to change your PIN.')}</p>
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              {t('common.close', 'Close')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4">{t('pin.change')}</h3>
        {success && (
          <div className="mb-3 text-sm text-green-600" role="status">
            {t('pin.changeSuccess')}
          </div>
        )}
        
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
                disabled={changePinMutation.isPending}
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
                disabled={changePinMutation.isPending}
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
                disabled={changePinMutation.isPending}
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
              disabled={changePinMutation.isPending}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={!!error || changePinMutation.isPending || !currentPin.trim() || !newPin.trim() || !confirmPin.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {changePinMutation.isPending ? t('common.loading') : t('pin.change')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PinChangeModal