'use client';

import React, { useState } from 'react';
import {
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

interface TelegramBulkActionsProps {
  selectedItems: string[];
  onAction: (action: string, itemIds: string[]) => Promise<void>;
  onClearSelection: () => void;
}

export default function TelegramBulkActions({
  selectedItems,
  onAction,
  onClearSelection
}: TelegramBulkActionsProps) {
  const [loading, setLoading] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<{
    action: string;
    title: string;
    description: string;
    danger?: boolean;
  } | null>(null);

  const actions = [
    {
      id: 'retry',
      label: 'Retry Selected',
      icon: ArrowPathIcon,
      description: 'Retry failed or pending items',
      buttonClass: 'bg-blue-600 hover:bg-blue-700 text-white',
      confirmTitle: 'Retry Selected Items',
      confirmDescription: `Are you sure you want to retry ${selectedItems.length} selected item(s)? This will re-queue them for processing.`
    },
    {
      id: 'cancel',
      label: 'Cancel Selected',
      icon: StopIcon,
      description: 'Cancel pending items',
      buttonClass: 'bg-red-600 hover:bg-red-700 text-white',
      confirmTitle: 'Cancel Selected Items',
      confirmDescription: `Are you sure you want to cancel ${selectedItems.length} selected item(s)? This action cannot be undone.`,
      danger: true
    },
    {
      id: 'priority_high',
      label: 'Set High Priority',
      icon: PlayIcon,
      description: 'Set selected items to high priority',
      buttonClass: 'bg-orange-600 hover:bg-orange-700 text-white',
      confirmTitle: 'Set High Priority',
      confirmDescription: `Set ${selectedItems.length} selected item(s) to high priority? They will be processed before normal priority items.`
    },
    {
      id: 'priority_normal',
      label: 'Set Normal Priority',
      icon: PlayIcon,
      description: 'Set selected items to normal priority',
      buttonClass: 'bg-gray-600 hover:bg-gray-700 text-white',
      confirmTitle: 'Set Normal Priority',
      confirmDescription: `Set ${selectedItems.length} selected item(s) to normal priority?`
    }
  ];

  const handleActionClick = (action: any) => {
    setPendingAction({
      action: action.id,
      title: action.confirmTitle,
      description: action.confirmDescription,
      danger: action.danger
    });
    setShowConfirmModal(true);
  };

  const handleConfirmAction = async () => {
    if (!pendingAction) return;

    try {
      setLoading(true);
      
      // Call the parent action handler
      await onAction(pendingAction.action, selectedItems);
      
      setShowConfirmModal(false);
      setPendingAction(null);
      
      // Show success message
      alert(`Bulk action "${pendingAction.action}" completed for ${selectedItems.length} items!`);
      
    } catch (error) {
      console.error('Bulk action failed:', error);
      alert(`Bulk action failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAction = () => {
    setShowConfirmModal(false);
    setPendingAction(null);
  };

  if (selectedItems.length === 0) {
    return null;
  }

  return (
    <>
      {/* Bulk Actions Bar */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected
              </h3>
              <p className="text-sm text-blue-600">
                Choose an action to apply to the selected queue items
              </p>
            </div>
          </div>

          <button
            onClick={onClearSelection}
            className="text-blue-600 hover:text-blue-800"
            title="Clear Selection"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Action Buttons */}
        <div className="mt-4 flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action.id}
              onClick={() => handleActionClick(action)}
              disabled={loading}
              className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed ${action.buttonClass}`}
              title={action.description}
            >
              <action.icon className="h-4 w-4 mr-2" />
              {action.label}
            </button>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="mt-4 text-sm text-blue-700">
          <span className="font-medium">{selectedItems.length}</span> items selected for bulk operation
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && pendingAction && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              {/* Modal Header */}
              <div className="flex items-center mb-4">
                {pendingAction.danger ? (
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mr-3" />
                ) : (
                  <CheckIcon className="h-6 w-6 text-blue-600 mr-3" />
                )}
                <h3 className="text-lg font-medium text-gray-900">
                  {pendingAction.title}
                </h3>
              </div>

              {/* Modal Content */}
              <div className="mb-6">
                <p className="text-sm text-gray-600">
                  {pendingAction.description}
                </p>
                
                {pendingAction.danger && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">
                      <strong>Warning:</strong> This action cannot be undone. Please confirm that you want to proceed.
                    </p>
                  </div>
                )}
              </div>

              {/* Modal Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={handleCancelAction}
                  disabled={loading}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmAction}
                  disabled={loading}
                  className={`px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                    pendingAction.danger
                      ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                      : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                  }`}
                >
                  {loading ? (
                    <div className="flex items-center">
                      <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" />
                      Processing...
                    </div>
                  ) : (
                    'Confirm'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}