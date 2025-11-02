import { Bell, Mail, Smartphone } from 'lucide-react';
import { useEffect, useState } from 'react';
import SaveSettingsChanges from './SaveSettingsChanges';
import {
  SettingsCard,
  SettingsContentWrapper,
  SettingsToggleCard,
  SettingsSeparator,
} from '../layout/SettingsLayout';
import {
  getUserNotificationSettings,
  NotificationSettingsResponse,
  NotificationSettingsUpdate,
  updateUserNotificationSettings,
} from '@/services/settingsService';
import { useMutation, useQuery } from '@tanstack/react-query';
import { snakeToCamel } from '@/utils/common';
import Loader from '@/components/ui/loader/Loader';
import Error from '@/components/ui/error/Error';
import { toast } from 'sonner';

const NotificationSettings = () => {
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    tutorialCompletions: true,
    newFeatures: true,
    weeklyDigest: true,
    browserNotifications: true,
  });

  const {
    data: notificationSettingsData,
    isPending,
    isFetching,
    error: errorNotificationSettings,
  } = useQuery({
    queryKey: ['notificationSettings'],
    queryFn: async () => {
      const response = await getUserNotificationSettings();
      const camelData = snakeToCamel<NotificationSettingsResponse>(response);
      setNotificationSettings({
        emailNotifications: camelData.email_notifications_enabled,
        tutorialCompletions: camelData.tutorial_completions,
        newFeatures: camelData.new_features,
        weeklyDigest: camelData.weekly_digest,
        browserNotifications: camelData.browser_notifications,
      });
      return camelData;
    },
    retry: false,
  });

  const updateNotificationMutation = useMutation({
    mutationFn: async (notificationSettings: NotificationSettingsUpdate) => {
      return await updateUserNotificationSettings({
        email_notifications_enabled:
          notificationSettings.email_notifications_enabled,
        tutorial_completions: notificationSettings.tutorial_completions,
        new_features: notificationSettings.new_features,
        weekly_digest: notificationSettings.weekly_digest,
        browser_notifications: notificationSettings.browser_notifications,
      });
    },
    onSuccess: () => {
      toast.success('Notification settings updated successfully!');
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail ||
          'Failed to update notification settings'
      );
    },
  });

  useEffect(() => {
    if (notificationSettingsData) {
      setNotificationSettings({
        emailNotifications:
          notificationSettingsData.email_notifications_enabled,
        tutorialCompletions: notificationSettingsData.tutorial_completions,
        newFeatures: notificationSettingsData.new_features,
        weeklyDigest: notificationSettingsData.weekly_digest,
        browserNotifications: notificationSettingsData.browser_notifications,
      });
    }
  }, [notificationSettingsData]);

  if (isPending || isFetching) {
    return (
      <Loader
        className="h-[300px] mt-25"
        type="ai"
        size="lg"
        message="Loading notification settings..."
      />
    );
  }

  if (errorNotificationSettings) {
    return (
      <Error
        title="Error loading notification settings"
        variant="full"
        className="!h-[500px]"
        error={errorNotificationSettings}
      />
    );
  }

  const handleNotificationSettingsChange = (
    setting: string,
    value: boolean
  ) => {
    setNotificationSettings({ ...notificationSettings, [setting]: value });
  };

  const handleSave = () => {
    updateNotificationMutation.mutate({
      email_notifications_enabled: notificationSettings.emailNotifications,
      tutorial_completions: notificationSettings.tutorialCompletions,
      new_features: notificationSettings.newFeatures,
      weekly_digest: notificationSettings.weeklyDigest,
      browser_notifications: notificationSettings.browserNotifications,
    });
  };

  return (
    <SettingsContentWrapper>
      <SettingsCard
        header={{
          icon: <Bell className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Email Notifications',
          description: 'Choose what emails you want to receive from Replo',
        }}
      >
        <SettingsToggleCard
          icon={<Mail className="w-5 h-5 text-blue-600 mr-1" />}
          title="Email Notifications"
          description="Receive email notifications for new messages, comments, and updates"
          checked={notificationSettings.emailNotifications}
          onChange={value =>
            handleNotificationSettingsChange('emailNotifications', value)
          }
        />
        <SettingsSeparator />
        <SettingsToggleCard
          bgColor=""
          title="Tutorial Completions"
          description="Get notified when you complete a tutorial"
          checked={notificationSettings.tutorialCompletions}
          onChange={value =>
            handleNotificationSettingsChange('tutorialCompletions', value)
          }
        />{' '}
        <SettingsToggleCard
          bgColor=""
          title="New Features"
          description="Updates about new features and improvements"
          checked={notificationSettings.newFeatures}
          onChange={value =>
            handleNotificationSettingsChange('newFeatures', value)
          }
        />
        <SettingsToggleCard
          bgColor=""
          title="Weekly Digest"
          description="Weekly summary of your learning progress"
          checked={notificationSettings.weeklyDigest}
          onChange={value =>
            handleNotificationSettingsChange('weeklyDigest', value)
          }
        />
      </SettingsCard>
      <SettingsCard
        header={{
          icon: <Smartphone className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Push Notifications',
          description: 'Manage browser push notifications',
        }}
      >
        <SettingsToggleCard
          icon={<Bell className="w-5 h-5 text-blue-600 mr-1" />}
          title="Browser Notifications"
          description="Get real-time updates in your browser"
          checked={notificationSettings.browserNotifications}
          onChange={value =>
            handleNotificationSettingsChange('browserNotifications', value)
          }
        />
      </SettingsCard>
      <SaveSettingsChanges handleSave={handleSave} />
    </SettingsContentWrapper>
  );
};

export default NotificationSettings;
