import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { UserCreate } from '@/api/types'

interface UserCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (userCreate: UserCreate) => void | Promise<void>
  isLoading?: boolean
}

const UserCreateModal: React.FC<UserCreateModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<UserCreate>({
    display_name: '',
    email: '',
    role: 'user',
    is_active: true,
    pin: '',
  })
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.display_name.trim()) {
      setError(t('user.displayNameRequired'))
      return
    }
    
    if (!formData.email.trim()) {
      setError(t('user.emailRequired'))
      return
    }
    
    if (!formData.pin.trim()) {
      setError(t('user.pinRequired'))
      return
    }
    
    if (formData.pin.length < 4) {
      setError(t('user.pinTooShort'))
      return
    }
    
    // Email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      setError(t('user.emailInvalid'))
      return
    }
    
    try {
      setError('')
      await onSubmit({ ...formData })
      // Reset form
      setFormData({
        display_name: '',
        email: '',
        role: 'user',
        is_active: true,
        pin: '',
      })
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const handleClose = () => {
    setError('')
    setFormData({
      display_name: '',
      email: '',
      role: 'user',
      is_active: true,
      pin: '',
    })
    onClose()
  }

  const handleInputChange = (field: keyof UserCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
        <h3 className="text-lg font-semibold mb-4">{t('user.createUser')}</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 mb-6">
            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.displayName')} *
              </label>
              <input
                type="text"
                id="display_name"
                value={formData.display_name}
                onChange={(e) => handleInputChange('display_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('user.displayNamePlaceholder')}
                disabled={isLoading}
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.email')} *
              </label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('user.emailPlaceholder')}
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.role')}
              </label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) => handleInputChange('role', e.target.value as 'user' | 'treasurer')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              >
                <option value="user">{t('user.userRole')}</option>
                <option value="treasurer">{t('user.treasurerRole')}</option>
              </select>
            </div>

            <div>
              <label htmlFor="qr_code" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.qrCode')}
              </label>
              <input
                type="text"
                id="qr_code"
                value={formData.qr_code || ''}
                onChange={(e) => handleInputChange('qr_code', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('user.qrCodePlaceholder')}
                disabled={isLoading}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active ?? true}
                onChange={(e) => handleInputChange('is_active', e.target.checked)}
                className="mr-2"
                disabled={isLoading}
              />
              <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                {t('common.active')}
              </label>
            </div>

            <div>
              <label htmlFor="pin" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.initialPin')} *
              </label>
              <input
                type="password"
                id="pin"
                value={formData.pin}
                onChange={(e) => handleInputChange('pin', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t('user.pinPlaceholder')}
                disabled={isLoading}
                maxLength={10}
              />
              <p className="text-xs text-gray-500 mt-1">
                {t('user.pinHelpText')}
              </p>
            </div>
          </div>

          {error && (
            <p className="text-red-500 text-sm mb-4">{error}</p>
          )}
          
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
              disabled={isLoading || !formData.display_name.trim() || !formData.email.trim() || !formData.pin.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('common.loading') : t('user.createUser')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default UserCreateModal