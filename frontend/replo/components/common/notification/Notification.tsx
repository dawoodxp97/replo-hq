'use client';

import {
  Badge,
  Popover,
  Skeleton,
  Typography,
  Empty,
  Divider,
  message,
} from 'antd';
import { Bell, CheckCircle2, AlertCircle, Info, Sparkles } from 'lucide-react';
import { memo, useState, useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import {
  borderGradientDefault,
  borderGradientHover,
  borderGradientFocus,
  backgroundGradientDefault,
  boxShadows,
  aiGradientBackground,
} from '@/constants/gradientColors';

const { Text } = Typography;

// Notification type definition
interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'default';
  created_at: string;
  read: boolean;
  link?: string;
}

// Notification type icons
const getNotificationIcon = (type: Notification['type']) => {
  const icons = {
    success: <CheckCircle2 className="w-4 h-4 text-green-500" />,
    info: <Info className="w-4 h-4 text-blue-500" />,
    warning: <AlertCircle className="w-4 h-4 text-orange-500" />,
    default: <Sparkles className="w-4 h-4 text-purple-500" />,
  };
  return icons[type] || icons.default;
};

// Format date for grouping
const formatDateGroup = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const notificationDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate()
  );

  if (notificationDate.getTime() === today.getTime()) {
    return 'Today';
  } else if (notificationDate.getTime() === yesterday.getTime()) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  }
};

// Group notifications by date
const groupNotificationsByDate = (
  notifications: Notification[]
): Record<string, Notification[]> => {
  return notifications.reduce((groups, notification) => {
    const dateGroup = formatDateGroup(notification.created_at);
    if (!groups[dateGroup]) {
      groups[dateGroup] = [];
    }
    groups[dateGroup].push(notification);
    return groups;
  }, {} as Record<string, Notification[]>);
};

// API response interface
interface NotificationListResponse {
  notifications: Notification[];
  unread_count: number;
}

// Fetch notifications
const fetchNotifications = async (): Promise<NotificationListResponse> => {
  try {
    const response: any = await apiClient.get(API_ENDPOINTS.NOTIFICATIONS_GET);
    // Support both AxiosResponse and plain data returns
    const data = response?.data ?? response;

    // Handle the response format from backend
    if (data && typeof data === 'object' && 'notifications' in data) {
      return {
        notifications: data.notifications || [],
        unread_count: data.unread_count || 0,
      };
    }

    // Fallback for old format (if API returns array directly)
    if (Array.isArray(data)) {
      return {
        notifications: data,
        unread_count: data.filter((n: Notification) => !n.read).length,
      };
    }

    return { notifications: [], unread_count: 0 };
  } catch (error) {
    console.error('Failed to fetch notifications:', error);
    return { notifications: [], unread_count: 0 };
  }
};

// Mark notification as read
const markNotificationAsRead = async (
  notificationId: string
): Promise<void> => {
  try {
    await apiClient.put(API_ENDPOINTS.NOTIFICATIONS_MARK_READ(notificationId));
  } catch (error) {
    console.error('Failed to mark notification as read:', error);
    throw error;
  }
};

// Mark all notifications as read
const markAllNotificationsAsRead = async (): Promise<void> => {
  try {
    await apiClient.put(API_ENDPOINTS.NOTIFICATIONS_MARK_ALL_READ);
  } catch (error) {
    console.error('Failed to mark all notifications as read:', error);
    throw error;
  }
};

const Notification = () => {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch notifications using useQuery
  const {
    data: notificationData,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<NotificationListResponse>({
    queryKey: ['notifications'],
    queryFn: fetchNotifications,
    enabled: true, // Enable auto-fetching
    refetchOnWindowFocus: true,
    staleTime: 30000, // Consider data stale after 30 seconds
    refetchInterval: 60000, // Refetch every minute when open
  });

  const notifications = notificationData?.notifications || [];
  const unreadCount = notificationData?.unread_count || 0;

  // Refetch notifications whenever dropdown opens
  useEffect(() => {
    if (open) {
      refetch();
    }
  }, [open, refetch]);

  // Handle mark as read
  const handleMarkAsRead = async (
    notification: Notification,
    e?: React.MouseEvent
  ) => {
    if (e) {
      e.stopPropagation();
    }

    if (notification.read) return;

    try {
      await markNotificationAsRead(notification.id);
      // Optimistically update the cache
      queryClient.setQueryData<NotificationListResponse>(
        ['notifications'],
        old => {
          if (!old) return old;
          return {
            notifications: old.notifications.map(n =>
              n.id === notification.id ? { ...n, read: true } : n
            ),
            unread_count: Math.max(0, old.unread_count - 1),
          };
        }
      );
    } catch (error) {
      message.error('Failed to mark notification as read');
    }
  };

  // Handle mark all as read
  const handleMarkAllAsRead = async () => {
    if (unreadCount === 0) return;

    try {
      await markAllNotificationsAsRead();
      // Optimistically update the cache
      queryClient.setQueryData<NotificationListResponse>(
        ['notifications'],
        old => {
          if (!old) return old;
          return {
            notifications: old.notifications.map(n => ({ ...n, read: true })),
            unread_count: 0,
          };
        }
      );
      message.success('All notifications marked as read');
    } catch (error) {
      message.error('Failed to mark all notifications as read');
    }
  };

  // Handle notification click
  const handleNotificationClick = async (notification: Notification) => {
    // Mark as read if unread
    if (!notification.read) {
      await handleMarkAsRead(notification);
    }

    // Navigate if link exists
    if (notification.link) {
      // Check if it's an absolute URL or relative path
      if (notification.link.startsWith('http')) {
        window.location.href = notification.link;
      } else {
        router.push(notification.link);
        setOpen(false);
      }
    }
  };

  // Group notifications by date
  const groupedNotifications = useMemo(() => {
    return groupNotificationsByDate(notifications);
  }, [notifications]);

  // Notification content
  const notificationContent = (
    <div className="notification-popover w-96 max-h-[600px] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-white to-gray-50">
        <Text strong className="text-base text-gray-900">
          Notifications
        </Text>
        {unreadCount > 0 && (
          <Badge
            className="notification-badge !bg-indigo-500 !text-white"
            count={unreadCount}
            size="small"
          />
        )}
      </div>

      {/* Content */}
      <div className="overflow-y-auto flex-1">
        {isLoading || isFetching ? (
          <div className="p-4 space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton active paragraph={{ rows: 2 }} />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <Empty
              description={
                <Text type="secondary">
                  Failed to load notifications. Please try again.
                </Text>
              }
            />
          </div>
        ) : Object.keys(groupedNotifications).length === 0 ? (
          <div className="p-8 text-center">
            <Empty
              description={<Text type="secondary">No notifications yet</Text>}
            />
          </div>
        ) : (
          <div className="py-2">
            {Object.entries(groupedNotifications).map(
              ([dateGroup, dateNotifications], groupIndex) => (
                <div key={dateGroup}>
                  {/* Date Separator Header */}
                  <div className="px-4 py-2">
                    <Typography.Text
                      type="secondary"
                      className="text-xs font-medium text-gray-500 uppercase tracking-wide"
                    >
                      {dateGroup}
                    </Typography.Text>
                  </div>

                  {/* Notifications for this date group */}
                  <div className="space-y-0">
                    {dateNotifications.map((notification, index) => (
                      <div
                        key={notification.id}
                        className={`notification-item px-4 py-3 cursor-pointer transition-all duration-200 hover:bg-gray-50 border-l-2 ${
                          notification.read
                            ? 'border-transparent bg-white'
                            : 'border-indigo-500 bg-indigo-50/30'
                        } ${
                          index < dateNotifications.length - 1
                            ? 'border-b border-gray-100'
                            : ''
                        }`}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex gap-3">
                          {/* Icon */}
                          <div className="flex-shrink-0 mt-0.5">
                            {getNotificationIcon(notification.type)}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <Text
                                strong
                                className={`text-sm ${
                                  notification.read
                                    ? 'text-gray-700'
                                    : 'text-gray-900'
                                }`}
                              >
                                {notification.title}
                              </Text>
                              {!notification.read && (
                                <div className="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0 mt-1.5" />
                              )}
                            </div>
                            <Text
                              type="secondary"
                              className="text-xs mt-1 block leading-relaxed"
                            >
                              {notification.message}
                            </Text>
                            <Text
                              type="secondary"
                              className="text-xs mt-2 block"
                              style={{ fontSize: '11px' }}
                            >
                              {new Date(
                                notification.created_at
                              ).toLocaleTimeString('en-US', {
                                hour: 'numeric',
                                minute: '2-digit',
                                hour12: true,
                              })}
                            </Text>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Divider separator after each date group (except last) */}
                  {groupIndex <
                    Object.keys(groupedNotifications).length - 1 && (
                    <Divider
                      style={{
                        margin: '8px 0',
                        borderColor: 'rgba(226, 232, 240, 0.8)',
                      }}
                    />
                  )}
                </div>
              )
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      {!isLoading &&
        !isFetching &&
        notifications.length > 0 &&
        unreadCount > 0 && (
          <div
            className="px-4 py-3 border-t border-gray-200 bg-gray-50"
            onClick={handleMarkAllAsRead}
          >
            <Text
              type="secondary"
              className="text-xs text-center block cursor-pointer hover:text-indigo-600 transition-colors"
            >
              Mark all as read
            </Text>
          </div>
        )}
    </div>
  );

  return (
    <div className="notification-container">
      <Popover
        content={notificationContent}
        trigger="click"
        open={open}
        onOpenChange={setOpen}
        placement="bottomRight"
        overlayClassName="notification-popover-overlay"
        overlayStyle={{ padding: 0 }}
      >
        <div className="gradient-border-wrapper">
          <Badge count={unreadCount} size="small" offset={[-2, 2]}>
            <button
              className="notification-button w-10 h-10 rounded-[10px] transition-all duration-200 flex items-center justify-center group flex-shrink-0 relative"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5 text-slate-600 group-hover:text-indigo-600 transition-colors" />
            </button>
          </Badge>
        </div>
      </Popover>

      {/* AI Gradient Border Styles */}
      <style jsx global>{`
        .ant-badge .ant-badge-count {
          background-color: #ad46ff !important;
          color: white !important;
          z-index: 1 !important;
        }
        /* Gradient border wrapper - AI-inspired design */
        .notification-container .gradient-border-wrapper {
          position: relative;
          border-radius: 0.75rem;
          padding: 1.5px;
          background: ${borderGradientDefault};
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .notification-container .gradient-border-wrapper:hover {
          background: ${borderGradientHover};
          box-shadow: ${boxShadows.hover};
        }

        /* Focus/Active state */
        .notification-container:has(.ant-popover-open)
          .gradient-border-wrapper {
          background: ${borderGradientFocus} !important;
          padding: 2px !important;
          box-shadow: ${boxShadows.focus} !important;
          transform: translateY(-1px) !important;
        }

        /* Button styling with AI gradient background */
        .notification-container .notification-button {
          border: none !important;
          background: ${backgroundGradientDefault} !important;
          box-shadow: ${boxShadows.default} !important;
          position: relative;
          z-index: 1;
        }

        .notification-container
          .gradient-border-wrapper:hover
          .notification-button {
          cursor: pointer;
          box-shadow: ${boxShadows.hover} !important;
        }

        .notification-container:has(.ant-popover-open) .notification-button {
          background: ${aiGradientBackground} !important;
        }

        /* Popover styling */
        .notification-popover-overlay .ant-popover-content {
          border-radius: 0.75rem;
          overflow: hidden;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1),
            0 4px 10px rgba(0, 0, 0, 0.05);
          border: 1px solid rgba(226, 232, 240, 0.8);
        }

        .notification-popover-overlay .ant-popover-inner {
          padding: 0;
          border-radius: 0.75rem;
        }

        .notification-popover-overlay .ant-popover-arrow {
          display: none;
        }

        /* Notification item hover effects */
        .notification-item {
          transition: all 0.2s ease;
        }

        .notification-item:hover {
          background: linear-gradient(
            135deg,
            rgba(99, 102, 241, 0.05) 0%,
            rgba(147, 51, 234, 0.05) 100%
          ) !important;
        }

        /* Scrollbar styling */
        .notification-popover::-webkit-scrollbar {
          width: 6px;
        }

        .notification-popover::-webkit-scrollbar-track {
          background: transparent;
        }

        .notification-popover::-webkit-scrollbar-thumb {
          background: rgba(148, 163, 184, 0.3);
          border-radius: 3px;
        }

        .notification-popover::-webkit-scrollbar-thumb:hover {
          background: rgba(148, 163, 184, 0.5);
        }
      `}</style>
    </div>
  );
};

export default memo(Notification);
