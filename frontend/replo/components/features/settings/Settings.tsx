'use client';

import { Constants } from '@/utils/common';
import { useState } from 'react';
import ProfileSettings from './components/ProfileSettings';
import NotificationSettings from './components/NotificationSettings';
import AppearanceSettings from './components/AppearanceSettings';
import LearningSettings from './components/LearningSettings';
import SecuritySettings from './components/SecuritySettings';
import ReploTabs from '@/components/ui/tabs/Tabs';

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
    <div className="rl-settings-container p-6 h-full overflow-auto">
      <div className="rl-settings-header h-[10%]">
        <h1 className="font-bold">Settings</h1>
        <span className="text-sm text-slate-500">
          Manage your account and preferences
        </span>
      </div>
      <div className="rl-settings-content h-[80%]">
        <ReploTabs kind="card" items={TABS} />
      </div>
      <div className="rl-settings-footer h-[10%]"></div>
    </div>
  );
}
