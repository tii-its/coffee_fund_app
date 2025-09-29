import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '@/store'
import UserSelectionModal from './UserSelectionModal'
import type { User } from '@/api/types'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireUserPin?: boolean
  requireTreasurerRole?: boolean
  sessionTimeout?: number // in milliseconds, default 1 hour
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireUserPin = true,
  requireTreasurerRole = false,
  sessionTimeout = 60 * 60 * 1000 // 1 hour
}) => {
  const { t } = useTranslation()
  const { 
    treasurerAuthenticated, 
    setTreasurerAuthenticated, 
    authTimestamp 
  } = useAppStore()
  
  const [showUserSelection, setShowUserSelection] = useState(false)
  const [authenticatedUser, setAuthenticatedUser] = useState<User | null>(null)

  // Check if authentication is still valid
  useEffect(() => {
    if (!requireUserPin) return
    
    const isAuthValid = treasurerAuthenticated && 
                       authTimestamp && 
                       (Date.now() - authTimestamp < sessionTimeout)
    
    if (!isAuthValid) {
      setTreasurerAuthenticated(false)
      setShowUserSelection(true)
      setAuthenticatedUser(null)
    }
  }, [treasurerAuthenticated, authTimestamp, requireUserPin, sessionTimeout, setTreasurerAuthenticated])

  // Show user selection modal if not authenticated and PIN is required
  useEffect(() => {
    if (requireUserPin && !treasurerAuthenticated) {
      setShowUserSelection(true)
    }
  }, [requireUserPin, treasurerAuthenticated])

  const handleUserSelected = async (user: User) => {
    // Check if treasurer role is required
    if (requireTreasurerRole && user.role !== 'treasurer') {
      throw new Error(t('auth.treasurerOnly'))
    }
    
    setAuthenticatedUser(user)
    setTreasurerAuthenticated(true)
    setShowUserSelection(false)
  }

  const handleModalClose = () => {
    // Don't allow closing if PIN is required and user is not authenticated
    if (requireUserPin && !treasurerAuthenticated) {
      return
    }
    setShowUserSelection(false)
  }

  // If PIN is required and user is not authenticated, show nothing until PIN is verified
  if (requireUserPin && !treasurerAuthenticated) {
    return (
      <>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🔒</div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">
              {t('auth.restricted')}
            </h2>
            <p className="text-gray-500 mb-6">
              {requireTreasurerRole ? t('auth.treasurerOnly') : t('auth.userPinRequired')}
            </p>
            <button 
              onClick={() => setShowUserSelection(true)}
              className="btn btn-primary"
            >
              {t('auth.selectUser')}
            </button>
          </div>
        </div>
        
        <UserSelectionModal
          isOpen={showUserSelection}
          onClose={handleModalClose}
          onUserSelected={handleUserSelected}
          title={requireTreasurerRole ? t('auth.treasurerAccess') : t('auth.userAccess')}
          description={requireTreasurerRole ? t('auth.treasurerAccessDescription') : t('auth.userAccessDescription')}
        />
      </>
    )
  }

  return <>{children}</>
}

export default ProtectedRoute