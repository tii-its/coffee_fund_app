import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { User } from '@/api/types'

interface UserPinInputModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (user: User, pin: string) => void | Promise<void>
  user?: User | null
  title?: string
  description?: string
  isLoading?: boolean
}

const UserPinInputModal: React.FC<UserPinInputModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  user,
  title,
  description,
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
    
    if (!user) {
      setError(t('user.notSelected'))
      return
    }
    
    try {
      setError('')
      await onSubmit(user, pin)
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
        <h3 className="text-lg font-semibold mb-2">
          {title || t('pin.userVerificationRequired')}
        </h3>
        
        {user && (
          <div className="mb-4 p-3 bg-gray-50 rounded-md">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold">
                  {user.display_name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <div className="font-medium text-gray-900">{user.display_name}</div>
                <div className="text-sm text-gray-500">{user.email}</div>
              </div>
            </div>
          </div>
        )}
        
        <p className="text-gray-600 mb-4">
          {description || t('pin.enterUserPinDescription')}
        </p>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="user-pin" className="block text-sm font-medium text-gray-700 mb-2">
              {t('pin.userPin')}
            </label>
            <input
              type="password"
              id="user-pin"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t('pin.placeholder')}
              disabled={isLoading}
              autoFocus
              maxLength={10}
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
              disabled={isLoading || !pin.trim() || !user}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('common.loading') : t('common.verify')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default UserPinInputModal