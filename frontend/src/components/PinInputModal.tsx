import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'

interface PinInputModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (pin: string) => void | Promise<void>
  title?: string
  description?: string
  isLoading?: boolean
}

const PinInputModal: React.FC<PinInputModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title = 'PIN Verification Required',
  description = 'Please enter the Admin PIN to continue.',
  isLoading = false,
}) => {
  const { t } = useTranslation()
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pin.trim()) {
      setError(t('pin.required'))
      return
    }
    
    try {
      setError('')
      await onSubmit(pin)
      // Do not call onClose here — caller should control modal visibility on successful submit.
      // This avoids triggering parent close handlers that perform navigation (e.g. redirect to home).
      setPin('')
    } catch (err: any) {
      setError(err.response?.data?.detail || t('pin.invalid'))
    }
  }

  const handleClose = () => {
    setPin('')
    setError('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-gray-600 mb-4">{description}</p>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="pin" className="block text-sm font-medium text-gray-700 mb-2">
              {t('pin.label')}
            </label>
            <input
              type="password"
              id="pin"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t('pin.placeholder')}
              disabled={isLoading}
              autoFocus
            />
            {error && (
              <p className="text-red-500 text-sm mt-1">{error}</p>
            )}
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading || !pin.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('common.loading') : t('common.submit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PinInputModal