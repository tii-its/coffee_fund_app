import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, moneyMovesApi, exportsApi, stockPurchasesApi } from '@/api/client'
import { useAppStore } from '@/store'
import { formatCurrency, formatDate, downloadBlob } from '@/lib/utils'
import StockPurchaseForm from '@/components/StockPurchaseForm'
import type { StockPurchaseCreate } from '@/api/types'

const Treasurer: React.FC = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { currentUser } = useAppStore()
  
  const [showStockForm, setShowStockForm] = useState(false)

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

  // Fetch stock purchases
  const { data: stockPurchases = [] } = useQuery({
    queryKey: ['stockPurchases'],
    queryFn: () => stockPurchasesApi.getAll().then((res) => res.data),
  })

  // Stock purchase mutations
  const createStockPurchaseMutation = useMutation({
    mutationFn: (stockPurchase: StockPurchaseCreate) => 
      stockPurchasesApi.create(stockPurchase, currentUser?.id || ''),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockPurchases'] })
      setShowStockForm(false)
    },
  })

  const processCashOutMutation = useMutation({
    mutationFn: (id: string) => 
      stockPurchasesApi.processCashOut(id, currentUser?.id || ''),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockPurchases'] })
    },
  })

  // Users below threshold
  const belowThreshold = balances.filter(balance => balance.balance_cents < 1000)
  
  // Stock purchases pending cash out
  const pendingCashOut = stockPurchases.filter(sp => !sp.is_cash_out_processed)
  const totalPendingCashOut = pendingCashOut.reduce((sum, sp) => sum + sp.total_amount_cents, 0)

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

  const handleStockPurchaseSubmit = async (stockPurchase: StockPurchaseCreate) => {
    await createStockPurchaseMutation.mutateAsync(stockPurchase)
  }

  const handleCashOut = async (id: string) => {
    if (window.confirm(t('stock.cashOutConfirmation', { 
      item: stockPurchases.find(sp => sp.id === id)?.item_name 
    }))) {
      await processCashOutMutation.mutateAsync(id)
    }
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
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
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">{t('stock.pendingCashOut')}</h3>
          <p className="text-2xl font-bold text-orange-600">{formatCurrency(totalPendingCashOut)}</p>
          <p className="text-sm text-gray-500">{pendingCashOut.length} {t('stock.purchases').toLowerCase()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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

        {/* Stock Purchases */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">{t('stock.purchases')}</h3>
            <button
              onClick={() => setShowStockForm(true)}
              className="btn btn-primary btn-sm"
            >
              + {t('stock.addPurchase')}
            </button>
          </div>
          
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {stockPurchases.length > 0 ? (
              stockPurchases.slice(0, 5).map((purchase) => (
                <div
                  key={purchase.id}
                  className="border rounded p-3"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-medium">{purchase.item_name}</p>
                      <p className="text-sm text-gray-500">
                        {purchase.quantity}x @ {formatCurrency(purchase.unit_price_cents)}
                      </p>
                    </div>
                    <p className="font-semibold text-blue-600">
                      {formatCurrency(purchase.total_amount_cents)}
                    </p>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {formatDate(purchase.purchase_date)}
                  </p>
                  
                  {!purchase.is_cash_out_processed && (
                    <button
                      onClick={() => handleCashOut(purchase.id)}
                      disabled={processCashOutMutation.isPending}
                      className="btn btn-warning btn-sm w-full"
                    >
                      {processCashOutMutation.isPending ? t('common.loading') : t('stock.processCashOut')}
                    </button>
                  )}
                  
                  {purchase.is_cash_out_processed && (
                    <div className="text-sm text-green-600 font-medium">
                      ✓ {t('stock.cashOutProcessed')}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                {t('stock.noPurchases')}
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
      
      {/* Stock Purchase Form Modal */}
      {showStockForm && (
        <StockPurchaseForm
          onSubmit={handleStockPurchaseSubmit}
          onCancel={() => setShowStockForm(false)}
          isLoading={createStockPurchaseMutation.isPending}
        />
      )}
    </div>
  )
}

export default Treasurer