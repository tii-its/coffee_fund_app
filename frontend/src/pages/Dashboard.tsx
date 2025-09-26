import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { usersApi, consumptionsApi, moneyMovesApi } from '@/api/client'
import { formatCurrency, formatDateShort } from '@/lib/utils'
import BalanceCard from '@/components/BalanceCard'
import UserPicker from '@/components/UserPicker'
import type { User } from '@/api/types'

const Dashboard: React.FC = () => {
  const { t } = useTranslation()
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

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

  // Fetch all user balances
  const { data: allBalances = [] } = useQuery({
    queryKey: ['allBalances'],
    queryFn: () => usersApi.getAllBalances().then((res) => res.data),
  })

  if (!selectedUser) {
    return (
      <div>
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-2">{t('kiosk.selectUser')}</h2>
          <p className="text-gray-600">{t('dashboard.currentBalance')}</p>
        </div>
        
        <UserPicker users={users} onSelect={setSelectedUser} />
        
        {/* Overview Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
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
            <h3 className="text-lg font-semibold mb-2">{t('treasurer.belowThreshold')}</h3>
            <p className="text-3xl font-bold text-red-600">
              {allBalances.filter(balance => balance.balance_cents < 1000).length}
            </p>
            <p className="text-gray-600 text-sm">&lt; €10.00</p>
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
        <div className="mb-6">
          <BalanceCard balance={userBalance} />
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
    </div>
  )
}

export default Dashboard