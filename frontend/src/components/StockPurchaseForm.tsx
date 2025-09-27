import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { StockPurchaseCreate } from '@/api/types'

interface StockPurchaseFormProps {
  onSubmit: (stockPurchase: StockPurchaseCreate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

const StockPurchaseForm: React.FC<StockPurchaseFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<StockPurchaseCreate>({
    item_name: '',
    supplier: '',
    quantity: 1,
    unit_price_cents: 0,
    total_amount_cents: 0,
    purchase_date: new Date().toISOString().split('T')[0], // Today's date
    receipt_number: '',
    notes: '',
  })

  const handleInputChange = (field: keyof StockPurchaseCreate, value: string | number) => {
    const newFormData = { ...formData, [field]: value }
    
    // Auto-calculate total when quantity or unit price changes
    if (field === 'quantity' || field === 'unit_price_cents') {
      newFormData.total_amount_cents = newFormData.quantity * newFormData.unit_price_cents
    }
    
    setFormData(newFormData)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Prepare data with proper types and date format
    const submitData: StockPurchaseCreate = {
      ...formData,
      purchase_date: new Date(formData.purchase_date).toISOString(),
      supplier: formData.supplier?.trim() || null,
      receipt_number: formData.receipt_number?.trim() || null,
      notes: formData.notes?.trim() || null,
    }
    
    await onSubmit(submitData)
  }

  const formatCents = (cents: number) => {
    return (cents / 100).toFixed(2)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4">{t('stock.addPurchase')}</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Item Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('stock.itemName')} *
            </label>
            <input
              type="text"
              value={formData.item_name}
              onChange={(e) => handleInputChange('item_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={isLoading}
            />
          </div>

          {/* Supplier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('stock.supplier')}
            </label>
            <input
              type="text"
              value={formData.supplier || ''}
              onChange={(e) => handleInputChange('supplier', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
          </div>

          {/* Quantity and Unit Price */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('common.quantity')} *
              </label>
              <input
                type="number"
                min="1"
                value={formData.quantity}
                onChange={(e) => handleInputChange('quantity', parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={isLoading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('stock.unitPrice')} (€) *
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formatCents(formData.unit_price_cents)}
                onChange={(e) => handleInputChange('unit_price_cents', Math.round(parseFloat(e.target.value || '0') * 100))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Total Amount (auto-calculated, read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('stock.totalAmount')} (€)
            </label>
            <input
              type="text"
              value={formatCents(formData.total_amount_cents)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
              readOnly
            />
          </div>

          {/* Purchase Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('stock.purchaseDate')} *
            </label>
            <input
              type="date"
              value={formData.purchase_date}
              onChange={(e) => handleInputChange('purchase_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={isLoading}
            />
          </div>

          {/* Receipt Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('stock.receiptNumber')}
            </label>
            <input
              type="text"
              value={formData.receipt_number || ''}
              onChange={(e) => handleInputChange('receipt_number', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('common.note')}
            </label>
            <textarea
              value={formData.notes || ''}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.item_name.trim() || formData.total_amount_cents <= 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default StockPurchaseForm