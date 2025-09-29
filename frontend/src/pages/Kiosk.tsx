import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, productsApi, consumptionsApi } from '@/api/client'
import { formatCurrency } from '@/lib/utils'
import UserPicker from '@/components/UserPicker'
import ProductGrid from '@/components/ProductGrid'
import type { User, Product } from '@/api/types'
import { useAppStore } from '@/store'

const Kiosk: React.FC = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { selectedUser, setSelectedUser } = useAppStore()
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [step, setStep] = useState<'user' | 'product' | 'confirm' | 'complete'>('user')

  // Fetch users and products
  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll({ active_only: true }).then((res) => res.data),
  })

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.getAll({ active_only: true }).then((res) => res.data),
  })

  // Get user balance
  const { data: userBalance } = useQuery({
    queryKey: ['userBalance', selectedUser?.id],
    queryFn: () => selectedUser ? usersApi.getBalance(selectedUser.id).then((res) => res.data) : null,
    enabled: !!selectedUser,
  })

  // Create consumption mutation
  const createConsumption = useMutation({
    mutationFn: (data: { user_id: string; product_id: string; qty: number; creator_id: string }) =>
      consumptionsApi.create(
        { user_id: data.user_id, product_id: data.product_id, qty: data.qty },
        data.creator_id
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userBalance'] })
      queryClient.invalidateQueries({ queryKey: ['consumptions'] })
      setStep('complete')
      setTimeout(() => {
        handleReset()
      }, 3000)
    },
  })

  const handleUserSelect = (user: User) => {
    setSelectedUser(user)
    setStep('product')
  }

  const handleProductSelect = (product: Product) => {
    setSelectedProduct(product)
    setStep('confirm')
  }

  const handleConfirmPurchase = () => {
    if (selectedUser && selectedProduct) {
      // For kiosk mode, we'll use the first treasurer as creator (in real app, might be a kiosk user)
      const treasurerUser = users.find(u => u.role === 'treasurer')
      if (treasurerUser) {
        createConsumption.mutate({
          user_id: selectedUser.id,
          product_id: selectedProduct.id,
          qty: quantity,
          creator_id: treasurerUser.id,
        })
      }
    }
  }

  const handleReset = () => {
    setSelectedUser(null)
    setSelectedProduct(null)
    setQuantity(1)
    setStep('user')
  }

  const totalAmount = selectedProduct ? selectedProduct.price_cents * quantity : 0
  const remainingBalance = userBalance ? userBalance.balance_cents - totalAmount : 0
  const isBelowThreshold = remainingBalance < 1000 // 10€ threshold

  return (
    <div className="max-w-6xl mx-auto">
      {/* Progress Indicator */}
      <div className="flex justify-center mb-8">
        <div className="flex items-center space-x-4">
          {['user', 'product', 'confirm'].map((stepName, index) => (
            <div key={stepName} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step === stepName || (index < ['user', 'product', 'confirm'].indexOf(step))
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {index + 1}
              </div>
              {index < 2 && (
                <div
                  className={`w-12 h-1 ${
                    index < ['user', 'product', 'confirm'].indexOf(step)
                      ? 'bg-blue-600'
                      : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      {step === 'user' && (
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-6">{t('kiosk.selectUser')}</h2>
          <UserPicker users={users} onSelect={handleUserSelect} selectedUserId={selectedUser?.id || null} />
        </div>
      )}

      {step === 'product' && selectedUser && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">{t('kiosk.selectProduct')}</h2>
            <div className="text-right">
              <p className="text-sm text-gray-600">{selectedUser.display_name}</p>
              <p className="font-semibold">
                {t('kiosk.userBalance')}: {formatCurrency(userBalance?.balance_cents || 0)}
              </p>
              {isBelowThreshold && (
                <p className="text-red-600 text-sm">{t('kiosk.belowThreshold')}</p>
              )}
            </div>
          </div>
          <ProductGrid products={products} onSelect={handleProductSelect} />
        </div>
      )}

      {step === 'confirm' && selectedUser && selectedProduct && (
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold text-center mb-6">{t('kiosk.confirmPurchase')}</h2>
          
          <div className="card">
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="font-medium">{t('common.user')}:</span>
                <span>{selectedUser.display_name}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="font-medium">{t('common.product')}:</span>
                <span>{selectedProduct.name}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="font-medium">{t('common.price')}:</span>
                <span>{formatCurrency(selectedProduct.price_cents)}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="font-medium">{t('common.quantity')}:</span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="btn btn-outline px-3 py-1"
                  >
                    -
                  </button>
                  <span className="px-4">{quantity}</span>
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="btn btn-outline px-3 py-1"
                  >
                    +
                  </button>
                </div>
              </div>
              
              <hr />
              
              <div className="flex justify-between text-lg font-semibold">
                <span>{t('common.total')}:</span>
                <span>{formatCurrency(totalAmount)}</span>
              </div>
              
              <div className="flex justify-between">
                <span>{t('kiosk.userBalance')}:</span>
                <span>{formatCurrency(userBalance?.balance_cents || 0)}</span>
              </div>
              
              <div className="flex justify-between">
                <span>{t('dashboard.currentBalance')} {t('common.total')}:</span>
                <span className={remainingBalance < 0 ? 'text-red-600' : 'text-green-600'}>
                  {formatCurrency(remainingBalance)}
                </span>
              </div>
              
              {isBelowThreshold && remainingBalance > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-yellow-800 text-sm">{t('kiosk.belowThreshold')}</p>
                </div>
              )}
              
              {remainingBalance < 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-red-800 text-sm">{t('errors.insufficientBalance')}</p>
                </div>
              )}
            </div>
            
            <div className="flex space-x-4 mt-6">
              <button onClick={handleReset} className="btn btn-secondary flex-1">
                {t('common.cancel')}
              </button>
              <button
                onClick={handleConfirmPurchase}
                disabled={createConsumption.isPending}
                className="btn btn-success flex-1"
              >
                {createConsumption.isPending ? (
                  <span className="loading" />
                ) : (
                  t('common.confirm')
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'complete' && (
        <div className="text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-green-600 mb-4">{t('kiosk.purchaseComplete')}</h2>
          <p className="text-gray-600">{t('common.loading')}...</p>
        </div>
      )}
    </div>
  )
}

export default Kiosk