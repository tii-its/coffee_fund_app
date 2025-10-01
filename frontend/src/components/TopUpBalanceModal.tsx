import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { formatCurrency } from '@/lib/utils'
import type { User, MoneyMoveCreate } from '@/api/types'

interface TopUpBalanceModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: MoneyMoveCreate) => void | Promise<void>
  user: User | null
  isLoading?: boolean
}

const TopUpBalanceModal: React.FC<TopUpBalanceModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  user,
  isLoading = false,
}) => {
  const { t } = useTranslation()
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) {
      setError(t('user.selectUser'))
      return
    }
    
    const amountValue = parseFloat(amount)
    if (!amount.trim() || isNaN(amountValue) || amountValue <= 0) {
      setError(t('moneyMove.invalidAmount'))
      return
    }
    
    const amountCents = Math.round(amountValue * 100)
    
    try {
      await onSubmit({
        type: 'deposit',
        user_id: user.id,
        amount_cents: amountCents,
        note: note.trim() || null,
      })
      
      // Reset form
      setAmount('')
      setNote('')
      setError('')
    } catch (err) {
      setError(t('moneyMove.creationFailed'))
    }
  }

  const handleClose = () => {
    setAmount('')
    setNote('')
    setError('')
    onClose()
  }

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    // Allow only numbers and decimal points
    if (/^\d*\.?\d*$/.test(value)) {
      setAmount(value)
      setError('')
    }
  }

  if (!isOpen) return null

  const amountInCents = amount ? Math.round(parseFloat(amount) * 100) : 0

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-bold mb-4">{t('moneyMove.topUpBalance')}</h2>
        
        {user && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <p className="font-medium">{user.display_name}</p>
            {/* email removed */}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('moneyMove.amount')} (€)
            </label>
            <input
              type="text"
              value={amount}
              onChange={handleAmountChange}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="10.00"
              step="0.01"
              min="0.01"
              disabled={isLoading}
            />
            {amount && (
              <p className="text-sm text-gray-500 mt-1">
                {t('common.equivalent')}: {formatCurrency(amountInCents)}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('moneyMove.note')} ({t('common.optional')})
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t('moneyMove.noteExample')}
              rows={3}
              maxLength={500}
              disabled={isLoading}
            />
            <p className="text-xs text-gray-500 mt-1">
              {note.length}/500 {t('common.characters')}
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-yellow-800 text-sm">
              {t('moneyMove.confirmationRequired')}
            </p>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading || !amount || !user}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {isLoading ? (
                <span className="flex items-center">
                  <span className="loading mr-2" />
                  {t('common.creating')}
                </span>
              ) : (
                t('moneyMove.requestTopUp')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TopUpBalanceModal