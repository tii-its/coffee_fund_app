import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import type { User, UserUpdate } from '@/api/types'

interface UserEditModalProps {
  isOpen: boolean
  onClose: () => void
  user: User | null
  onSubmit: (userUpdate: UserUpdate, pin: string) => void | Promise<void>
  isLoading?: boolean
}

const UserEditModal: React.FC<UserEditModalProps> = ({
  isOpen,
  onClose,
  user,
  onSubmit,
  isLoading = false,
}) => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<UserUpdate>({})
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (user) {
      setFormData({
        display_name: user.display_name,
  // email removed
        role: user.role,
        is_active: user.is_active,
        qr_code: user.qr_code || undefined,
      })
    }
  }, [user])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pin.trim()) {
      setError(t('pin.required'))
      return
    }
    
    try {
      setError('')
      await onSubmit(formData, pin)
      setPin('')
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('common.error'))
    }
  }

  const handleClose = () => {
    setPin('')
    setError('')
    setFormData({})
    onClose()
  }

  const handleInputChange = (field: keyof UserUpdate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  if (!isOpen || !user) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
        <h3 className="text-lg font-semibold mb-4">{t('user.editUser')}</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 mb-6">
            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.displayName')}
              </label>
              <input
                type="text"
                id="display_name"
                value={formData.display_name || ''}
                onChange={(e) => handleInputChange('display_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
            </div>

            {/* Email field removed */}

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-2">
                {t('user.role')}
              </label>
              <select
                id="role"
                value={formData.role || 'user'}
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
          </div>

          <div className="mb-4">
              {/* Email field removed */}
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
              {isLoading ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default UserEditModal