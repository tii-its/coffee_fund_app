import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import UserSelectionModal from '@/components/UserSelectionModal'
import { usersApi } from '@/api/client'
import type { User } from '@/api/types'

interface TreasurerRouteProps {
  children: React.ReactNode
}

const TreasurerRoute: React.FC<TreasurerRouteProps> = ({ children }) => {
  const { t } = useTranslation()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showUserSelection, setShowUserSelection] = useState(true)
  const [authenticatedUser, setAuthenticatedUser] = useState<User | null>(null)

  const handleUserSelected = async (user: User) => {
    // Check if user has treasurer role
    if (user.role !== 'treasurer') {
      throw new Error(t('auth.treasurerOnly'))
    }
    
    setAuthenticatedUser(user)
    setIsAuthenticated(true)
    setShowUserSelection(false)
  }

  const handleUserSelectionClose = () => {
    // If user closes without authentication, redirect to home
    window.location.href = '/'
  }

  if (!isAuthenticated) {
    return (
      <UserSelectionModal
        isOpen={showUserSelection}
        onClose={handleUserSelectionClose}
        onUserSelected={handleUserSelected}
        title={t('auth.treasurerAccess')}
        description={t('auth.treasurerAccessDescription')}
      />
    )
  }

  return <>{children}</>
}

export default TreasurerRoute