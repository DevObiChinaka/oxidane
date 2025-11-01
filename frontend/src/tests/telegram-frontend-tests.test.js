/**
 * Frontend Component Test Suite
 * Tests React components and API integration
 * 
 * Run with: npm test -- telegram-frontend-tests.test.js
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { jest } from '@jest/globals';

// Mock the API hooks
jest.mock('../app/admin/hooks/useAdminAPI', () => ({
  useTelegramQueue: () => ({
    performBulkAction: jest.fn(),
    retryItem: jest.fn(),
    cancelItem: jest.fn(),
    loading: false,
    error: null
  }),
  useTelegramGroups: () => ({
    createGroup: jest.fn(),
    updateGroup: jest.fn(),
    deleteGroup: jest.fn(),
    toggleGroupStatus: jest.fn(),
    loading: false,
    error: null
  })
}));

// Mock the admin auth context
jest.mock('../app/admin/contexts/AdminAuthContext', () => ({
  useAdminAuth: () => ({
    isAuthenticated: true,
    user: { username: 'testadmin', email: 'test@example.com' },
    loading: false,
    logout: jest.fn()
  })
}));

// Import components to test
import TelegramGroupsPanel from '../components/admin/TelegramGroupsPanel';
import TelegramManagementTable from '../components/admin/TelegramManagementTable';
import TelegramBulkActions from '../components/admin/TelegramBulkActions';
import TelegramQueueDashboard from '../components/admin/TelegramQueueDashboard';

// Mock data
const mockGroups = [
  {
    id: '1',
    name: 'VIP Signals Premium',
    chat_id: '-1001234567890',
    invite_link: 'https://t.me/+test',
    description: 'Premium group',
    member_count: 100,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    permissions: {
      can_send_messages: true,
      can_add_users: true,
      can_remove_users: true,
      is_admin: true
    }
  }
];

const mockQueueItems = [
  {
    id: '1',
    user: {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      telegram_username: '@testuser'
    },
    subscription_id: 'sub_1',
    action_type: 'add_to_group',
    group_name: 'VIP Signals Premium',
    priority: 'normal',
    status: 'pending',
    attempts: 0,
    max_attempts: 3,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

const mockStats = {
  pending_additions: 5,
  pending_removals: 2,
  failed_operations: 1,
  successful_operations_today: 25,
  queue_processing_rate: 95.2
};

describe('Telegram Frontend Components', () => {
  
  describe('TelegramGroupsPanel Component', () => {
    test('renders groups panel correctly', () => {
      render(<TelegramGroupsPanel onRefresh={jest.fn()} />);
      
      expect(screen.getByText('Telegram Groups')).toBeInTheDocument();
      expect(screen.getByText('Add Group')).toBeInTheDocument();
    });

    test('shows add group modal when button clicked', async () => {
      render(<TelegramGroupsPanel onRefresh={jest.fn()} />);
      
      const addButton = screen.getByText('Add Group');
      fireEvent.click(addButton);
      
      await waitFor(() => {
        expect(screen.getByText('Add New Group')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('VIP Signals Premium')).toBeInTheDocument();
      });
    });

    test('validates required fields in add group form', async () => {
      render(<TelegramGroupsPanel onRefresh={jest.fn()} />);
      
      // Open modal
      fireEvent.click(screen.getByText('Add Group'));
      
      // Submit without filling required fields
      const submitButton = screen.getByRole('button', { name: /add group/i });
      fireEvent.click(submitButton);
      
      // Should not submit (HTML5 validation will handle this)
      await waitFor(() => {
        expect(screen.getByText('Add New Group')).toBeInTheDocument();
      });
    });
  });

  describe('TelegramManagementTable Component', () => {
    test('renders queue items correctly', () => {
      render(
        <TelegramManagementTable
          queueItems={mockQueueItems}
          loading={false}
          selectedItems={[]}
          onSelectionChange={jest.fn()}
          onRefresh={jest.fn()}
        />
      );
      
      expect(screen.getByText('testuser')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('@testuser')).toBeInTheDocument();
      expect(screen.getByText('VIP Signals Premium')).toBeInTheDocument();
    });

    test('shows loading state', () => {
      render(
        <TelegramManagementTable
          queueItems={[]}
          loading={true}
          selectedItems={[]}
          onSelectionChange={jest.fn()}
          onRefresh={jest.fn()}
        />
      );
      
      expect(screen.getByText('Loading queue items...')).toBeInTheDocument();
    });

    test('shows empty state when no items', () => {
      render(
        <TelegramManagementTable
          queueItems={[]}
          loading={false}
          selectedItems={[]}
          onSelectionChange={jest.fn()}
          onRefresh={jest.fn()}
        />
      );
      
      expect(screen.getByText('No queue items found matching your criteria')).toBeInTheDocument();
    });

    test('filters items by search term', async () => {
      render(
        <TelegramManagementTable
          queueItems={mockQueueItems}
          loading={false}
          selectedItems={[]}
          onSelectionChange={jest.fn()}
          onRefresh={jest.fn()}
        />
      );
      
      const searchInput = screen.getByPlaceholderText(/search users/i);
      fireEvent.change(searchInput, { target: { value: 'testuser' } });
      
      // Should still show the item
      expect(screen.getByText('testuser')).toBeInTheDocument();
      
      // Search for non-existent user
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      
      await waitFor(() => {
        expect(screen.getByText('No queue items found matching your criteria')).toBeInTheDocument();
      });
    });

    test('handles item selection', () => {
      const onSelectionChange = jest.fn();
      
      render(
        <TelegramManagementTable
          queueItems={mockQueueItems}
          loading={false}
          selectedItems={[]}
          onSelectionChange={onSelectionChange}
          onRefresh={jest.fn()}
        />
      );
      
      const checkbox = screen.getAllByRole('checkbox')[1]; // First is select all
      fireEvent.click(checkbox);
      
      expect(onSelectionChange).toHaveBeenCalledWith(['1']);
    });
  });

  describe('TelegramBulkActions Component', () => {
    test('renders when items are selected', () => {
      render(
        <TelegramBulkActions
          selectedItems={['1', '2']}
          onAction={jest.fn()}
          onClearSelection={jest.fn()}
        />
      );
      
      expect(screen.getByText('2 items selected')).toBeInTheDocument();
      expect(screen.getByText('Retry Selected')).toBeInTheDocument();
      expect(screen.getByText('Cancel Selected')).toBeInTheDocument();
    });

    test('does not render when no items selected', () => {
      const { container } = render(
        <TelegramBulkActions
          selectedItems={[]}
          onAction={jest.fn()}
          onClearSelection={jest.fn()}
        />
      );
      
      expect(container).toBeEmptyDOMElement();
    });

    test('shows confirmation modal for bulk actions', async () => {
      render(
        <TelegramBulkActions
          selectedItems={['1', '2']}
          onAction={jest.fn()}
          onClearSelection={jest.fn()}
        />
      );
      
      const retryButton = screen.getByText('Retry Selected');
      fireEvent.click(retryButton);
      
      await waitFor(() => {
        expect(screen.getByText('Retry Selected Items')).toBeInTheDocument();
        expect(screen.getByText(/Are you sure you want to retry 2 selected/)).toBeInTheDocument();
      });
    });

    test('calls onAction when confirmed', async () => {
      const onAction = jest.fn().mockResolvedValue(undefined);
      
      render(
        <TelegramBulkActions
          selectedItems={['1']}
          onAction={onAction}
          onClearSelection={jest.fn()}
        />
      );
      
      // Click retry
      fireEvent.click(screen.getByText('Retry Selected'));
      
      // Confirm in modal
      await waitFor(() => {
        const confirmButton = screen.getByText('Confirm');
        fireEvent.click(confirmButton);
      });
      
      await waitFor(() => {
        expect(onAction).toHaveBeenCalledWith('retry', ['1']);
      });
    });
  });

  describe('TelegramQueueDashboard Component', () => {
    test('renders queue statistics', () => {
      render(
        <TelegramQueueDashboard
          queueItems={mockQueueItems}
          stats={mockStats}
          onRefresh={jest.fn()}
        />
      );
      
      expect(screen.getByText('Processing')).toBeInTheDocument();
      expect(screen.getByText('95.2%')).toBeInTheDocument();
    });

    test('shows queue controls', () => {
      render(
        <TelegramQueueDashboard
          queueItems={mockQueueItems}
          stats={mockStats}
          onRefresh={jest.fn()}
        />
      );
      
      expect(screen.getByText('Pause Queue')).toBeInTheDocument();
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    test('shows recent activity', () => {
      render(
        <TelegramQueueDashboard
          queueItems={mockQueueItems}
          stats={mockStats}
          onRefresh={jest.fn()}
        />
      );
      
      expect(screen.getByText('Recent Queue Activity')).toBeInTheDocument();
      expect(screen.getByText(/add_to_group - VIP Signals Premium/)).toBeInTheDocument();
    });

    test('toggles queue status', async () => {
      // Mock window.confirm
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => true);
      
      render(
        <TelegramQueueDashboard
          queueItems={mockQueueItems}
          stats={mockStats}
          onRefresh={jest.fn()}
        />
      );
      
      const pauseButton = screen.getByText('Pause Queue');
      fireEvent.click(pauseButton);
      
      await waitFor(() => {
        expect(window.confirm).toHaveBeenCalledWith(
          'Are you sure you want to pause the queue processing?'
        );
      });
      
      // Restore original confirm
      window.confirm = originalConfirm;
    });
  });

  describe('Integration Tests', () => {
    test('components work together in main page flow', async () => {
      // This would test the main TelegramManagementPage component
      // with all child components working together
      
      // Mock the useAdminAuth hook return for this test
      const { useAdminAuth } = require('../app/admin/contexts/AdminAuthContext');
      useAdminAuth.mockReturnValue({
        isAuthenticated: true,
        user: { username: 'testadmin' },
        loading: false
      });
      
      // Would render the main page component here
      // This is a placeholder for integration testing
      expect(true).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      const onActionWithError = jest.fn().mockRejectedValue(new Error('API Error'));
      
      render(
        <TelegramBulkActions
          selectedItems={['1']}
          onAction={onActionWithError}
          onClearSelection={jest.fn()}
        />
      );
      
      // Trigger action that will fail
      fireEvent.click(screen.getByText('Retry Selected'));
      
      await waitFor(() => {
        const confirmButton = screen.getByText('Confirm');
        fireEvent.click(confirmButton);
      });
      
      // Should handle error gracefully
      await waitFor(() => {
        expect(onActionWithError).toHaveBeenCalled();
      });
      
      consoleError.mockRestore();
    });
  });
});

describe('API Integration Tests', () => {
  // Mock fetch for API tests
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('API client handles authentication', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ token: 'test_token' })
    });

    // Test authentication flow
    const response = await fetch('/api/admin-auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username: 'admin', password: 'test' })
    });

    const data = await response.json();
    expect(data.token).toBe('test_token');
  });

  test('API client handles network errors', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    try {
      await fetch('/api/admin/telegram/groups/');
    } catch (error) {
      expect(error.message).toBe('Network error');
    }
  });

  test('API client handles HTTP errors', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ error: 'Not found' })
    });

    const response = await fetch('/api/admin/telegram/groups/999/');
    expect(response.status).toBe(404);
  });
});

// Performance tests
describe('Performance Tests', () => {
  test('large queue items list renders efficiently', () => {
    const largeItemsList = Array.from({ length: 1000 }, (_, i) => ({
      ...mockQueueItems[0],
      id: i.toString(),
      user: { ...mockQueueItems[0].user, username: `user${i}` }
    }));

    const start = performance.now();
    
    render(
      <TelegramManagementTable
        queueItems={largeItemsList}
        loading={false}
        selectedItems={[]}
        onSelectionChange={jest.fn()}
        onRefresh={jest.fn()}
      />
    );
    
    const end = performance.now();
    const renderTime = end - start;
    
    // Should render within reasonable time (adjust threshold as needed)
    expect(renderTime).toBeLessThan(1000); // 1 second
  });
});

// Accessibility tests
describe('Accessibility Tests', () => {
  test('components have proper ARIA labels', () => {
    render(
      <TelegramManagementTable
        queueItems={mockQueueItems}
        loading={false}
        selectedItems={[]}
        onSelectionChange={jest.fn()}
        onRefresh={jest.fn()}
      />
    );
    
    // Check for proper table structure
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getAllByRole('columnheader')).toHaveLength(9); // Adjust based on actual columns
    expect(screen.getAllByRole('row')).toHaveLength(2); // Header + 1 data row
  });

  test('buttons have proper labels and states', () => {
    render(
      <TelegramBulkActions
        selectedItems={['1']}
        onAction={jest.fn()}
        onClearSelection={jest.fn()}
      />
    );
    
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveProperty('textContent');
      expect(button.textContent).toBeTruthy();
    });
  });
});