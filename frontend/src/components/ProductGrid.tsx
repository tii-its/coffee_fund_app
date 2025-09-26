import React from 'react'
import { formatCurrency } from '@/lib/utils'
import type { Product } from '@/api/types'

interface ProductGridProps {
  products: Product[]
  onSelect: (product: Product) => void
}

const ProductGrid: React.FC<ProductGridProps> = ({ products, onSelect }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
      {products.map((product) => (
        <button
          key={product.id}
          onClick={() => onSelect(product)}
          className="card hover:shadow-lg transition-shadow p-6 text-center"
        >
          <div className="text-4xl mb-2">☕</div>
          <p className="font-medium text-gray-900 mb-1">{product.name}</p>
          <p className="text-lg font-semibold text-blue-600">
            {formatCurrency(product.price_cents)}
          </p>
        </button>
      ))}
    </div>
  )
}

export default ProductGrid