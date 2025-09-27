import React, { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { Product } from '@/api/types'

const productSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  price_cents: z.number().min(1, 'Price must be greater than 0'),
  is_active: z.boolean().optional().default(true),
})

type ProductFormData = z.infer<typeof productSchema>

interface ProductModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: ProductFormData) => void
  product?: Product | null
  title: string
}

export const ProductModal: React.FC<ProductModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  product,
  title,
}) => {
  const { t } = useTranslation()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      name: '',
      price_cents: 100, // Default to 1 euro in cents
      is_active: true,
    },
  })

  // Reset form when product prop changes
  useEffect(() => {
    if (product) {
      reset({
        name: product.name,
        price_cents: product.price_cents,
        is_active: product.is_active,
      })
    } else {
      reset({
        name: '',
        price_cents: 100,
        is_active: true,
      })
    }
  }, [product, reset])

  // Convert cents to euros for display
  const priceInEuros = (watch('price_cents') || 0) / 100

  const handleFormSubmit = (data: ProductFormData) => {
    onSubmit(data)
    reset()
    onClose()
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const euros = parseFloat(e.target.value) || 0
    const cents = Math.round(euros * 100)
    setValue('price_cents', cents)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('product.name')}
            </label>
            <input
              type="text"
              {...register('name')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Coffee, Tea, etc."
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('product.price')}
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                min="0"
                value={priceInEuros.toFixed(2)}
                onChange={handlePriceChange}
                className="w-full border border-gray-300 rounded-md px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="1.50"
              />
              <span className="absolute right-3 top-2 text-gray-500">€</span>
            </div>
            {errors.price_cents && (
              <p className="text-red-500 text-sm mt-1">{errors.price_cents.message}</p>
            )}
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                {...register('is_active')}
                className="form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm font-medium text-gray-700">
                {t('common.active')}
              </span>
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}