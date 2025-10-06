import React from 'react'
import { useTranslation } from 'react-i18next'

interface UserDeleteConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  onForceConfirm: () => void
  userName: string
  hasRelatedRecords: boolean
  relatedRecords?: {
    consumptions?: boolean
    created_consumptions?: boolean
    money_moves?: boolean
    created_money_moves?: boolean
    confirmed_money_moves?: boolean
    audit_entries?: boolean
  }
}

const UserDeleteConfirmationModal: React.FC<UserDeleteConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  onForceConfirm,
  userName,
  hasRelatedRecords,
  relatedRecords
}) => {
  const { t } = useTranslation()

  if (!isOpen) return null

  const getRelatedRecordsList = () => {
    if (!relatedRecords) return []
    
    const records = []
    if (relatedRecords.consumptions) records.push(t('user.deleteConfirmation.records.consumptions', 'Consumptions'))
    if (relatedRecords.created_consumptions) records.push(t('user.deleteConfirmation.records.createdConsumptions', 'Created consumptions'))
    if (relatedRecords.money_moves) records.push(t('user.deleteConfirmation.records.moneyMoves', 'Money moves'))
    if (relatedRecords.created_money_moves) records.push(t('user.deleteConfirmation.records.createdMoneyMoves', 'Created money moves'))
    if (relatedRecords.confirmed_money_moves) records.push(t('user.deleteConfirmation.records.confirmedMoneyMoves', 'Confirmed money moves'))
    if (relatedRecords.audit_entries) records.push(t('user.deleteConfirmation.records.auditEntries', 'Audit entries'))
    
    return records
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {t('user.deleteUser')}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-6">
          {hasRelatedRecords ? (
            <>
              <div className="flex items-center mb-3">
                <div className="flex-shrink-0 w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-gray-900">
                    {t('user.deleteConfirmation.warningTitle', 'User has related records')}
                  </h4>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-3">
                {t('user.deleteConfirmation.warningMessage', 
                  'The user "{{userName}}" has related records. Deleting will permanently deactivate the user but keep their history for data integrity.', 
                  { userName }
                )}
              </p>

              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
                <p className="text-sm font-medium text-yellow-800 mb-2">
                  {t('user.deleteConfirmation.relatedRecords', 'Related records:')}
                </p>
                <ul className="text-sm text-yellow-700 list-disc list-inside space-y-1">
                  {getRelatedRecordsList().map((record, index) => (
                    <li key={index}>{record}</li>
                  ))}
                </ul>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                {t('user.deleteConfirmation.consequences', 
                  'After deletion, the user will be permanently deactivated and cannot be restored, but their transaction history will be preserved.'
                )}
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-600 mb-4">
              {t('user.deleteConfirmation.simpleMessage', 
                'Are you sure you want to permanently delete the user "{{userName}}"? This action cannot be undone.', 
                { userName }
              )}
            </p>
          )}
        </div>

        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            {t('common.cancel')}
          </button>
          
          {hasRelatedRecords ? (
            <button
              data-testid="force-deactivate-btn"
              onClick={onForceConfirm}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              {t('user.deleteConfirmation.deactivate', 'Deactivate User')}
            </button>
          ) : (
            <button
              data-testid="confirm-delete-btn"
              onClick={onConfirm}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              {t('user.deleteConfirmation.delete', 'Delete User')}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default UserDeleteConfirmationModal