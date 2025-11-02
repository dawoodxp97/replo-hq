import { Bell, Mail, Smartphone } from 'lucide-react';
import { useState } from 'react';
import SaveSettingsChanges from './SaveSettingsChanges';
import {
  SettingsCard,
  SettingsContentWrapper,
  SettingsToggleCard,
  SettingsSeparator,
} from '../layout/SettingsLayout';

const NotificationSettings = () => {
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    tutorialCompletions: true,
    newFeatures: true,
    weeklyDigest: true,
    browserNotifications: true,
  });

  const handleNotificationSettingsChange = (
    setting: string,
    value: boolean
  ) => {
    setNotificationSettings({ ...notificationSettings, [setting]: value });
  };

  const handleSave = () => {
    console.log('Saving notification settings');
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
