import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import PinInputModal from '@/components/PinInputModal'
import { usersApi } from '@/api/client'

interface TreasurerRouteProps {
  children: React.ReactNode
}

const TreasurerRoute: React.FC<TreasurerRouteProps> = ({ children }) => {
  const { t } = useTranslation()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showPinModal, setShowPinModal] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  const handlePinSubmit = async (pin: string) => {
    setIsLoading(true)
    try {
      await usersApi.verifyPin(pin)
      setIsAuthenticated(true)
      setShowPinModal(false)
    } catch (error) {
      throw error // Let PinInputModal handle the error display
    } finally {
      setIsLoading(false)
    }
  }

  const handlePinModalClose = () => {
    // If user closes without authentication, redirect to home
    window.location.href = '/'
  }

  if (!isAuthenticated) {
    return (
      <PinInputModal
        isOpen={showPinModal}
        onClose={handlePinModalClose}
        onSubmit={handlePinSubmit}
        title={t('pin.treasurerAccess')}
        description={t('pin.treasurerAccessDescription')}
        isLoading={isLoading}
      />
    )
  }

  return <>{children}</>
}

export default TreasurerRoute