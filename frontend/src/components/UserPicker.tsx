import React from 'react'
import type { User } from '@/api/types'

interface UserPickerProps {
  users: User[]
  onSelect: (user: User) => void
  selectedUserId?: string | null
}

const UserPicker: React.FC<UserPickerProps> = ({ users, onSelect, selectedUserId }) => {
  if (!users.length) {
    return (
      <p className="text-gray-500 text-center" data-testid="no-users">
        No users available. Create users first.
      </p>
    )
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-w-4xl mx-auto" data-testid="user-picker">
      {users.map((user) => {
        const isSelected = user.id === selectedUserId
        return (
          <button
            key={user.id}
            type="button"
            onClick={() => onSelect(user)}
            className={`card hover:shadow-lg transition-all p-6 text-center border-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              isSelected ? 'border-blue-600 shadow-md scale-[1.02]' : 'border-transparent'
            }`}
            data-testid={`user-btn-${user.id}`}
          >
            <div className="text-4xl mb-2">👤</div>
            <p className="font-medium text-gray-900">{user.display_name}</p>
            <p className="text-sm text-gray-500 capitalize">{user.role}</p>
            {isSelected && (
              <span className="mt-2 inline-block text-xs text-blue-600 font-semibold" data-testid="selected-indicator">
                Selected
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

export default UserPicker