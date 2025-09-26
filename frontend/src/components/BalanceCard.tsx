import React from 'react'
import { useTranslation } from 'react-i18next'
import { formatCurrency } from '@/lib/utils'
import type { UserBalance } from '@/api/types'

interface BalanceCardProps {
  balance: UserBalance
}

const BalanceCard: React.FC<BalanceCardProps> = ({ balance }) => {
  const { t } = useTranslation()
  const isLow = balance.balance_cents < 1000 // Below €10
  const isNegative = balance.balance_cents < 0

  return (
    <div className={`card ${isNegative ? 'bg-red-50 border-red-200' : isLow ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{t('dashboard.currentBalance')}</h3>
          <p className="text-sm text-gray-600">{balance.user.display_name}</p>
        </div>
        <div className="text-right">
          <p className={`text-3xl font-bold ${
            isNegative ? 'text-red-600' : isLow ? 'text-yellow-600' : 'text-green-600'
          }`}>
            {formatCurrency(balance.balance_cents)}
          </p>
          {isLow && !isNegative && (
            <p className="text-sm text-yellow-600">{t('kiosk.belowThreshold')}</p>
          )}
          {isNegative && (
            <p className="text-sm text-red-600">{t('errors.insufficientBalance')}</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default BalanceCard