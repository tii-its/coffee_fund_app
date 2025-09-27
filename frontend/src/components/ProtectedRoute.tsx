import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '@/store'
import { usersApi } from '@/api/client'
import PinInputModal from './PinInputModal'

interface ProtectedRouteProps {
  children: React.ReactNode
  requirePin?: boolean
  sessionTimeout?: number // in milliseconds, default 1 hour
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requirePin = true,
  sessionTimeout = 60 * 60 * 1000 // 1 hour
}) => {
  const { t } = useTranslation()
  const { 
    treasurerAuthenticated, 
    setTreasurerAuthenticated, 
    authTimestamp 
  } = useAppStore()
  
  const [showPinModal, setShowPinModal] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Check if authentication is still valid
  useEffect(() => {
    if (!requirePin) return
    
    const isAuthValid = treasurerAuthenticated && 
                       authTimestamp && 
                       (Date.now() - authTimestamp < sessionTimeout)
    
    if (!isAuthValid) {
      setTreasurerAuthenticated(false)
      setShowPinModal(true)
    }
  }, [treasurerAuthenticated, authTimestamp, requirePin, sessionTimeout, setTreasurerAuthenticated])

  // Show PIN modal if not authenticated and PIN is required
  useEffect(() => {
    if (requirePin && !treasurerAuthenticated) {
      setShowPinModal(true)
    }
  }, [requirePin, treasurerAuthenticated])

  const handlePinSubmit = async (pin: string) => {
    setIsLoading(true)
    try {
      await usersApi.verifyPin(pin)
      setTreasurerAuthenticated(true)
      setShowPinModal(false)
    } catch (error: any) {
      throw error // PinInputModal will handle the error display
    } finally {
      setIsLoading(false)
    }
  }

  const handleModalClose = () => {
    // Don't allow closing if PIN is required and user is not authenticated
    if (requirePin && !treasurerAuthenticated) {
      return
    }
    setShowPinModal(false)
  }

  // If PIN is required and user is not authenticated, show nothing until PIN is verified
  if (requirePin && !treasurerAuthenticated) {
    return (
      <>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🔒</div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">
              {t('auth.restricted')}
            </h2>
            <p className="text-gray-500 mb-6">
              {t('auth.treasurerOnly')}
            </p>
            <button 
              onClick={() => setShowPinModal(true)}
              className="btn btn-primary"
            >
              {t('auth.enterPin')}
            </button>
          </div>
        </div>
        
        <PinInputModal
          isOpen={showPinModal}
          onClose={handleModalClose}
          onSubmit={handlePinSubmit}
          isLoading={isLoading}
          title={t('auth.treasurerAccess')}
          description={t('auth.enterTreasurerPin')}
        />
      </>
    )
  }

  return <>{children}</>
}

export default ProtectedRoute