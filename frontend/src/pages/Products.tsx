import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi } from '@/api/client'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useAppStore } from '@/store'
import { ProductModal } from '@/components/ProductModal'
import { DeleteConfirmModal } from '@/components/DeleteConfirmModal'
import type { Product, ProductCreate, ProductUpdate } from '@/api/types'

type ProductFormData = {
  name: string
  price_cents: number
  is_active: boolean
}

const Products: React.FC = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { currentUser } = useAppStore()
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)

  const { data: products = [], isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.getAll({ active_only: false }).then((res) => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (product: ProductCreate) => 
      productsApi.create(product, currentUser?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setIsCreateModalOpen(false)
      // TODO: Add success toast notification
    },
    onError: (error) => {
      console.error('Failed to create product:', error)
      // TODO: Add error toast notification
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, product }: { id: string; product: ProductUpdate }) =>
      productsApi.update(id, product, currentUser?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setIsEditModalOpen(false)
      setSelectedProduct(null)
      // TODO: Add success toast notification
    },
    onError: (error) => {
      console.error('Failed to update product:', error)
      // TODO: Add error toast notification
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productsApi.delete(id, currentUser?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setIsDeleteModalOpen(false)
      setSelectedProduct(null)
      // TODO: Add success toast notification
    },
    onError: (error) => {
      console.error('Failed to delete product:', error)
      // TODO: Add error toast notification
    }
  })

  const handleCreateProduct = (product: ProductFormData) => {
    createMutation.mutate(product as ProductCreate)
  }

  const handleEditProduct = (product: ProductFormData) => {
    if (selectedProduct) {
      updateMutation.mutate({
        id: selectedProduct.id,
        product: product as ProductUpdate
      })
    }
  }

  const handleDeleteProduct = () => {
    if (selectedProduct) {
      deleteMutation.mutate(selectedProduct.id)
    }
  }

  const openEditModal = (product: Product) => {
    setSelectedProduct(product)
    setIsEditModalOpen(true)
  }

  const openDeleteModal = (product: Product) => {
    setSelectedProduct(product)
    setIsDeleteModalOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">{t('navigation.products')}</h2>
        <button 
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {t('product.createProduct')}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('product.name')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('product.price')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.status')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.date')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">☕</div>
                      <p className="font-medium text-gray-900">{product.name}</p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <p className="font-semibold text-blue-600">
                      {formatCurrency(product.price_cents)}
                    </p>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      product.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {product.is_active ? t('common.active') : t('common.inactive')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {formatDate(product.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => openEditModal(product)}
                        className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                      >
                        {t('common.edit')}
                      </button>
                      {product.is_active && (
                        <button 
                          onClick={() => openDeleteModal(product)}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                        >
                          {t('common.delete')}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {products.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>{t('errors.fetchFailed')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Product Modal */}
      <ProductModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateProduct}
        title={t('product.createProduct')}
      />

      {/* Edit Product Modal */}
      <ProductModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false)
          setSelectedProduct(null)
        }}
        onSubmit={handleEditProduct}
        product={selectedProduct}
        title={t('product.editProduct')}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setSelectedProduct(null)
        }}
        onConfirm={handleDeleteProduct}
        title={t('common.delete')}
        message={`Are you sure you want to deactivate "${selectedProduct?.name}"? This action cannot be undone.`}
      />
    </div>
  )
}

export default Products