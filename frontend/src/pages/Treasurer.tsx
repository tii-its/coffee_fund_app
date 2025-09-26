import React from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { usersApi, moneyMovesApi, exportsApi } from '@/api/client'
import { formatCurrency, formatDate, downloadBlob } from '@/lib/utils'

const Treasurer: React.FC = () => {
  const { t } = useTranslation()

  // Fetch all user balances
  const { data: balances = [] } = useQuery({
    queryKey: ['allBalances'],
    queryFn: () => usersApi.getAllBalances().then((res) => res.data),
  })

  // Fetch pending money moves
  const { data: pendingMoves = [] } = useQuery({
    queryKey: ['pendingMoves'],
    queryFn: () => moneyMovesApi.getPending().then((res) => res.data),
  })

  // Users below threshold
  const belowThreshold = balances.filter(balance => balance.balance_cents < 1000)

  const handleExport = async (type: 'consumptions' | 'moneyMoves' | 'balances') => {
    try {
      let response
      let filename
      
      switch (type) {
        case 'consumptions':
          response = await exportsApi.consumptions()
          filename = 'consumptions.csv'
          break
        case 'moneyMoves':
          response = await exportsApi.moneyMoves()
          filename = 'money_moves.csv'
          break
        case 'balances':
          response = await exportsApi.balances()
          filename = 'balances.csv'
          break
      }
      
      downloadBlob(response.data, filename)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">{t('common.total')} {t('navigation.users')}</h3>
          <p className="text-3xl font-bold text-blue-600">{balances.length}</p>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">{t('common.total')} {t('common.balance')}</h3>
          <p className="text-3xl font-bold text-green-600">
            {formatCurrency(balances.reduce((sum, b) => sum + b.balance_cents, 0))}
          </p>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">{t('treasurer.belowThreshold')}</h3>
          <p className="text-3xl font-bold text-red-600">{belowThreshold.length}</p>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">{t('moneyMove.pendingMoves')}</h3>
          <p className="text-3xl font-bold text-yellow-600">{pendingMoves.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Balances */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">{t('treasurer.userBalances')}</h3>
            <button
              onClick={() => handleExport('balances')}
              className="btn btn-outline btn-sm"
            >
              {t('treasurer.exportBalances')}
            </button>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {balances.map((balance) => (
              <div
                key={balance.user.id}
                className="flex justify-between items-center py-2 px-3 rounded border"
              >
                <div>
                  <p className="font-medium">{balance.user.display_name}</p>
                  <p className="text-sm text-gray-500 capitalize">{balance.user.role}</p>
                </div>
                <p className={`font-semibold ${
                  balance.balance_cents < 0 ? 'text-red-600' : 
                  balance.balance_cents < 1000 ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {formatCurrency(balance.balance_cents)}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Pending Money Moves */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">{t('moneyMove.pendingMoves')}</h3>
            <button
              onClick={() => handleExport('moneyMoves')}
              className="btn btn-outline btn-sm"
            >
              {t('treasurer.exportMoneyMoves')}
            </button>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {pendingMoves.length > 0 ? (
              pendingMoves.map((move) => (
                <div
                  key={move.id}
                  className="border rounded p-3"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-medium">{move.user.display_name}</p>
                      <p className="text-sm text-gray-500 capitalize">
                        {t(`moneyMove.${move.type}`)}
                      </p>
                    </div>
                    <p className={`font-semibold ${
                      move.type === 'deposit' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {move.type === 'deposit' ? '+' : '-'}{formatCurrency(move.amount_cents)}
                    </p>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {formatDate(move.created_at)}
                  </p>
                  
                  {move.note && (
                    <p className="text-sm text-gray-600 mb-2">"{move.note}"</p>
                  )}
                  
                  <div className="flex space-x-2">
                    <button className="btn btn-success btn-sm flex-1">
                      {t('common.confirm')}
                    </button>
                    <button className="btn btn-danger btn-sm flex-1">
                      {t('common.reject')}
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                {t('moneyMove.pendingMoves')} 
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Export Section */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">{t('treasurer.exportData')}</h3>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => handleExport('consumptions')}
            className="btn btn-primary"
          >
            {t('treasurer.exportConsumptions')}
          </button>
          <button
            onClick={() => handleExport('moneyMoves')}
            className="btn btn-primary"
          >
            {t('treasurer.exportMoneyMoves')}
          </button>
          <button
            onClick={() => handleExport('balances')}
            className="btn btn-primary"
          >
            {t('treasurer.exportBalances')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Treasurer