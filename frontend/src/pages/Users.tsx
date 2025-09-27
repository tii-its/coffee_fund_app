import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { usersApi } from '@/api/client'
import { formatDate } from '@/lib/utils'
import UserCreateModal from '@/components/UserCreateModal'

const Users: React.FC = () => {
  const { t } = useTranslation()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll().then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="loading"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">{t('navigation.users')}</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setIsCreateModalOpen(true)}
        >
          {t('user.createUser')}
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('user.displayName')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('user.email')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('user.role')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.status')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.date')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">👤</div>
                      <div>
                        <p className="font-medium text-gray-900">{user.display_name}</p>
                        {user.qr_code && (
                          <p className="text-sm text-gray-500">QR: {user.qr_code}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <p className="text-gray-900">{user.email}</p>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${
                      user.role === 'treasurer' ? 'badge-info' : 'badge-success'
                    }`}>
                      {t(`user.${user.role}Role`)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${
                      user.is_active ? 'badge-success' : 'badge-danger'
                    }`}>
                      {user.is_active ? t('common.active') : t('common.inactive')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex space-x-2">
                      <button className="btn btn-outline btn-sm">
                        {t('common.edit')}
                      </button>
                      <button className="btn btn-outline btn-sm">
                        QR
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <UserCreateModal 
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        // Note: In a real app, you'd pass the current user's ID
        // creatorId={currentUser?.id}
      />
    </div>
  )
}

export default Users