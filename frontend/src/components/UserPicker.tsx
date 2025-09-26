import React from 'react'
import type { User } from '@/api/types'

interface UserPickerProps {
  users: User[]
  onSelect: (user: User) => void
}

const UserPicker: React.FC<UserPickerProps> = ({ users, onSelect }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
      {users.map((user) => (
        <button
          key={user.id}
          onClick={() => onSelect(user)}
          className="card hover:shadow-lg transition-shadow p-6 text-center"
        >
          <div className="text-4xl mb-2">👤</div>
          <p className="font-medium text-gray-900">{user.display_name}</p>
          <p className="text-sm text-gray-500 capitalize">{user.role}</p>
        </button>
      ))}
    </div>
  )
}

export default UserPicker