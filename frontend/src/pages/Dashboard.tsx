import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, consumptionsApi, moneyMovesApi, productsApi } from '@/api/client'
import { formatCurrency, formatDateShort } from '@/lib/utils'
import { useAppStore } from '@/store'
import BalanceCard from '@/components/BalanceCard'
import UserSelectionModal from '@/components/UserSelectionModal'
import TopUpBalanceModal from '@/components/TopUpBalanceModal'
import type { User, MoneyMoveCreate } from '@/api/types'

const Dashboard: React.FC = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { currentUser } = useAppStore()
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isTopUpModalOpen, setIsTopUpModalOpen] = useState(false)
  const [isUserSelectionOpen, setIsUserSelectionOpen] = useState(false)

  // Fetch all users for selection
  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll({ active_only: true }).then((res) => res.data),
  })

  // Fetch user balance when selected
  const { data: userBalance } = useQuery({
    queryKey: ['userBalance', selectedUser?.id],
    queryFn: () => selectedUser ? usersApi.getBalance(selectedUser.id).then((res) => res.data) : null,
    enabled: !!selectedUser,
  })

  // Fetch recent consumptions for selected user
  const { data: recentConsumptions = [] } = useQuery({
    queryKey: ['recentConsumptions', selectedUser?.id],
    queryFn: () =>
      selectedUser
        ? consumptionsApi.getUserRecent(selectedUser.id, 5).then((res) => res.data)
        : [],
    enabled: !!selectedUser,
  })

  // Fetch pending money moves for selected user
  const { data: pendingMoves = [] } = useQuery({
    queryKey: ['pendingMoves', selectedUser?.id],
    queryFn: () =>
      selectedUser
        ? moneyMovesApi.getAll({ user_id: selectedUser.id, status: 'pending' }).then((res) => res.data)
        : [],
    enabled: !!selectedUser,
  })

  // Fetch users above threshold (>=€10.00) 
  const { data: usersAboveThreshold = [] } = useQuery({
    queryKey: ['usersAboveThreshold'],
    queryFn: () => usersApi.getAboveThreshold(1000).then((res) => res.data),
  })

  // Create money move mutation
  const createMoneyMoveMutation = useMutation({
    mutationFn: (data: MoneyMoveCreate) =>
      moneyMovesApi.create(data, currentUser?.id || ''),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingMoves'] })
      queryClient.invalidateQueries({ queryKey: ['userBalance'] })
      setIsTopUpModalOpen(false)
    },
  })

  const handleUserSelected = (user: User) => {
    setSelectedUser(user)
    setIsUserSelectionOpen(false)
  }

  const handleSelectUser = () => {
    setIsUserSelectionOpen(true)
  }

  const handleTopUpBalance = async (data: MoneyMoveCreate) => {
    try {
      await createMoneyMoveMutation.mutateAsync(data)
    } catch (error) {
      console.error('Failed to create money move:', error)
      throw error
    }
  }
  const { data: allBalances = [] } = useQuery({
    queryKey: ['allBalances'],
    queryFn: () => usersApi.getAllBalances().then((res) => res.data),
  })

  // Fetch users below €5 threshold
  const { data: usersBelowThreshold = [] } = useQuery({
    queryKey: ['usersBelowThreshold'],
    queryFn: () => usersApi.getBelowThreshold(500).then((res) => res.data), // 500 cents = €5
  })

  // Fetch latest added product
  const { data: latestProduct } = useQuery({
    queryKey: ['latestProduct'],
    queryFn: () => productsApi.getLatest().then((res) => res.data),
  })

  // Fetch product consumption statistics
  const { data: productConsumptionStats = [] } = useQuery({
    queryKey: ['productConsumptionStats'],
    queryFn: () => productsApi.getTopConsumers(3).then((res) => res.data), // Top 3 consumers per product
  })

  if (!selectedUser) {
    return (
      <div>
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-2">{t('dashboard.title')}</h2>
          <p className="text-gray-600">{t('dashboard.selectUserDescription')}</p>
        </div>
        
        <div className="text-center">
          <button
            onClick={handleSelectUser}
            className="btn btn-primary btn-lg"
          >
            {t('user.selectUser')}
          </button>
        </div>
        
        {/* Overview Cards */}
        <div className="mt-8 space-y-6">
          {/* First Row - Main Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold mb-2">{t('treasurer.userBalances')}</h3>
              <p className="text-3xl font-bold text-blue-600">{allBalances.length}</p>
              <p className="text-gray-600 text-sm">{t('navigation.users')}</p>
            </div>
            
            <div className="card">
              <h3 className="text-lg font-semibold mb-2">{t('common.total')} {t('common.balance')}</h3>
              <p className="text-3xl font-bold text-green-600">
                {formatCurrency(
                  allBalances.reduce((sum, balance) => sum + balance.balance_cents, 0)
                )}
              </p>
              <p className="text-gray-600 text-sm">{t('treasurer.userBalances')}</p>
            </div>
            
            <div className="card">
              <h3 className="text-lg font-semibold mb-2">{t('treasurer.aboveThreshold')}</h3>
              <p className="text-3xl font-bold text-green-600">
                {usersAboveThreshold.length}
              </p>
              <p className="text-gray-600 text-sm">≥ €10.00</p>
              {usersAboveThreshold.length > 0 && (
                <div className="mt-3 space-y-1">
                  {usersAboveThreshold.map((userBalance) => (
                    <div key={userBalance.user.id} className="text-sm text-gray-700 flex justify-between">
                      <span>{userBalance.user.display_name}</span>
                      <span className="text-green-600 font-medium">
                        {formatCurrency(userBalance.balance_cents)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Second Row - New Features */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Users Below €5 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-2">Users Below €5</h3>
              <p className="text-3xl font-bold text-red-600">
                {usersBelowThreshold.length}
              </p>
              <p className="text-gray-600 text-sm">Need to recharge</p>
              {usersBelowThreshold.length > 0 && (
                <div className="mt-3 space-y-1 max-h-32 overflow-y-auto">
                  {usersBelowThreshold.map((userBalance) => (
                    <div key={userBalance.user.id} className="text-sm text-gray-700 flex justify-between">
                      <span>{userBalance.user.display_name}</span>
                      <span className="text-red-600 font-medium">
                        {formatCurrency(userBalance.balance_cents)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Latest Product */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-2">Latest Added Product</h3>
              {latestProduct ? (
                <div>
                  <p className="text-2xl font-bold text-blue-600">{latestProduct.name}</p>
                  <p className="text-lg text-green-600 font-medium">
                    {formatCurrency(latestProduct.price_cents)}
                  </p>
                  <p className="text-gray-600 text-sm">
                    Added {formatDateShort(latestProduct.created_at)}
                  </p>
                </div>
              ) : (
                <p className="text-gray-500">No products available</p>
              )}
            </div>
          </div>

          {/* Third Row - Product Consumption Stats */}
          <div className="grid grid-cols-1 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Top Consumers by Product</h3>
              {productConsumptionStats.length > 0 ? (
                <div className="space-y-4">
                  {productConsumptionStats.map((productStats) => (
                    <div key={productStats.product.id} className="border-b border-gray-100 pb-4 last:border-b-0">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-blue-600">{productStats.product.name}</h4>
                        <span className="text-sm text-gray-500">
                          {formatCurrency(productStats.product.price_cents)}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        {productStats.top_consumers.map((consumer, index) => (
                          <div key={consumer.user_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div>
                              <span className="text-xs font-medium text-gray-500">#{index + 1}</span>
                              <p className="text-sm font-medium">{consumer.display_name}</p>
                              <p className="text-xs text-gray-600">{consumer.total_qty} items</p>
                            </div>
                            <span className="text-sm font-medium text-red-600">
                              {formatCurrency(consumer.total_amount_cents)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No consumption data available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* User Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">{selectedUser.display_name}</h2>
          <p className="text-gray-600 capitalize">{selectedUser.role}</p>
        </div>
        <button
          onClick={() => setSelectedUser(null)}
          className="btn btn-outline"
        >
          {t('kiosk.selectUser')}
        </button>
      </div>

      {/* Balance Card */}
      {userBalance && (
        <div className="mb-6 flex items-center gap-4">
          <div className="flex-1">
            <BalanceCard balance={userBalance} />
          </div>
          {currentUser?.role === 'treasurer' && (
            <button
              onClick={() => setIsTopUpModalOpen(true)}
              className="btn btn-success px-4 py-2"
            >
              {t('moneyMove.topUpBalance')}
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">{t('dashboard.recentActivity')}</h3>
          {recentConsumptions.length > 0 ? (
            <div className="space-y-3">
              {recentConsumptions.map((consumption) => (
                <div
                  key={consumption.id}
                  className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0"
                >
                  <div>
                    <p className="font-medium">{consumption.product.name}</p>
                    <p className="text-sm text-gray-500">
                      {consumption.qty}x • {formatDateShort(consumption.at)}
                    </p>
                  </div>
                  <p className="font-semibold text-red-600">
                    -{formatCurrency(consumption.amount_cents)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">{t('consumption.recentConsumptions')} </p>
          )}
        </div>

        {/* Pending Confirmations */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">{t('dashboard.pendingConfirmations')}</h3>
          {pendingMoves.length > 0 ? (
            <div className="space-y-3">
              {pendingMoves.map((move) => (
                <div
                  key={move.id}
                  className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0"
                >
                  <div>
                    <p className="font-medium capitalize">
                      {t(`moneyMove.${move.type}`)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatDateShort(move.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${
                      move.type === 'deposit' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {move.type === 'deposit' ? '+' : '-'}{formatCurrency(move.amount_cents)}
                    </p>
                    <p className="text-xs text-yellow-600 uppercase font-medium">
                      {t('moneyMove.pending')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">{t('moneyMove.pendingMoves')}</p>
          )}
        </div>
      </div>

      {/* Top Up Balance Modal */}
      <TopUpBalanceModal
        isOpen={isTopUpModalOpen}
        onClose={() => setIsTopUpModalOpen(false)}
        onSubmit={handleTopUpBalance}
        user={selectedUser}
        isLoading={createMoneyMoveMutation.isPending}
      />

      {/* User Selection Modal */}
      <UserSelectionModal
        isOpen={isUserSelectionOpen}
        onClose={() => setIsUserSelectionOpen(false)}
        onUserSelected={handleUserSelected}
        title={t('user.selectUser')}
        description={t('dashboard.userSelectionDescription')}
      />
    </div>
  )
}

export default Dashboard