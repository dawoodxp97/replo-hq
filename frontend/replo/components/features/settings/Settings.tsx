'use client';

import { Constants } from '@/utils/common';
import { useState } from 'react';
import ProfileSettings from './components/ProfileSettings';
import NotificationSettings from './components/NotificationSettings';
import AppearanceSettings from './components/AppearanceSettings';
import LearningSettings from './components/LearningSettings';
import SecuritySettings from './components/SecuritySettings';
import ReploTabs from '@/components/ui/tabs/Tabs';
import { Button, Typography } from 'antd';
import { Save } from 'lucide-react';

const TABS = [
  {
    key: Constants.SETTING_TABS_IDS.PROFILE,
    label: 'Profile',
    children: <ProfileSettings />,
  },
  {
    key: Constants.SETTING_TABS_IDS.NOTIFICATIONS,
    label: 'Notifications',
    children: <NotificationSettings />,
  },
  {
    key: Constants.SETTING_TABS_IDS.APPEARANCE,
    label: 'Appearance',
    children: <AppearanceSettings />,
  },
  {
    key: Constants.SETTING_TABS_IDS.LEARNING,
    label: 'Learning',
    children: <LearningSettings />,
  },
  {
    key: Constants.SETTING_TABS_IDS.SECURITY,
    label: 'Security',
    children: <SecuritySettings />,
  },
];

export function Settings() {
  return (
    <div className="rl-settings-container pt-6 pb-6 h-[calc(100vh-70px)]">
      <div className="rl-settings-header h-[10%] ml-6">
        <Typography.Title level={3} className="font-bold !mb-0">
          Settings
        </Typography.Title>
        <Typography.Text className="!text-sm !text-slate-500 !mb-0">
          Manage your account and preferences
        </Typography.Text>
      </div>
      <div className="rl-settings-content h-[90%]">
        <ReploTabs kind="card" items={TABS} />
      </div>
    </div>
  );
}
