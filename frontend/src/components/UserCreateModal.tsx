import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/api/client'
import type { UserCreate } from '@/api/types'

interface UserCreateModalProps {
  isOpen: boolean
  onClose: () => void
  creatorId?: string
}

const UserCreateModal: React.FC<UserCreateModalProps> = ({ isOpen, onClose, creatorId }) => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  
  const [formData, setFormData] = useState<UserCreate>({
    display_name: '',
    email: '',
    role: 'user',
    is_active: true
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const createUserMutation = useMutation({
    mutationFn: (data: UserCreate) => usersApi.create(data, creatorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setFormData({ display_name: '', email: '', role: 'user', is_active: true })
      setErrors({})
      onClose()
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.message
      if (message.includes('display name')) {
        setErrors({ display_name: message })
      } else if (message.includes('email')) {
        setErrors({ email: message })
      } else {
        setErrors({ general: message })
      }
    }
  })

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Display name is required'
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.email)) {
        newErrors.email = 'Please enter a valid email address'
      }
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      createUserMutation.mutate(formData)
    }
  }

  const handleInputChange = (field: keyof UserCreate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4">{t('user.createUser')}</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="alert alert-error">{errors.general}</div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('user.displayName')}
            </label>
            <input
              type="text"
              value={formData.display_name}
              onChange={(e) => handleInputChange('display_name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md ${
                errors.display_name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={t('user.displayName')}
            />
            {errors.display_name && (
              <p className="text-red-500 text-sm mt-1">{errors.display_name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('user.email')}
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md ${
                errors.email ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder={t('user.email')}
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1">{errors.email}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('user.role')}
            </label>
            <select
              value={formData.role}
              onChange={(e) => handleInputChange('role', e.target.value as 'user' | 'treasurer')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="user">{t('user.userRole')}</option>
              <option value="treasurer">{t('user.treasurerRole')}</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="mr-2"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
              {t('common.active')}
            </label>
          </div>

          <div className="flex justify-end space-x-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-outline"
              disabled={createUserMutation.isPending}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createUserMutation.isPending}
            >
              {createUserMutation.isPending ? t('common.loading') : t('common.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default UserCreateModal