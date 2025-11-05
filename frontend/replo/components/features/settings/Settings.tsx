'use client';

import { useMemo, useState } from 'react';
import { Typography } from 'antd';

import { Constants } from '@/utils/common';

import ReploTabs from '@/components/ui/tabs/Tabs';
import AppearanceSettings from './components/AppearanceSettings';
import LearningSettings from './components/LearningSettings';
import NotificationSettings from './components/NotificationSettings';
import ProfileSettings from './components/ProfileSettings';
import SecuritySettings from './components/SecuritySettings';

type TabComponent = React.ComponentType;

const TAB_CONFIG: Array<{
  key: string;
  label: string;
  component: TabComponent;
}> = [
  {
    key: Constants.SETTING_TABS_IDS.PROFILE,
    label: 'Profile',
    component: ProfileSettings,
  },
  {
    key: Constants.SETTING_TABS_IDS.NOTIFICATIONS,
    label: 'Notifications',
    component: NotificationSettings,
  },
  {
    key: Constants.SETTING_TABS_IDS.APPEARANCE,
    label: 'Appearance',
    component: AppearanceSettings,
  },
  {
    key: Constants.SETTING_TABS_IDS.LEARNING,
    label: 'Learning',
    component: LearningSettings,
  },
  {
    key: Constants.SETTING_TABS_IDS.SECURITY,
    label: 'Security',
    component: SecuritySettings,
  },
];

export function Settings() {
  const [activeKey, setActiveKey] = useState<string>(
    Constants.SETTING_TABS_IDS.PROFILE
  );

  // Only render the active tab's component to ensure it mounts/unmounts on tab change
  // This ensures useQuery hooks refetch when navigating between tabs
  const tabs = useMemo(() => {
    return TAB_CONFIG.map(tab => {
      const Component = tab.component;
      return {
        key: tab.key,
        label: tab.label,
        children: activeKey === tab.key ? <Component key={tab.key} /> : null,
      };
    });
  }, [activeKey]);

  return (
    <div className="rl-settings-container pt-6 pb-6 !max-w-[calc(100vw-220px)] !h-[calc(100vh-90px)] overflow-hidden">
      <div className="rl-settings-header h-[10%] ml-6">
        <Typography.Title level={3} className="font-bold !mb-0">
          Settings
        </Typography.Title>
        <Typography.Text className="!text-sm !text-slate-500 !mb-0">
          Manage your account and preferences
        </Typography.Text>
      </div>
      <div className="rl-settings-content h-[90%]">
        <ReploTabs
          kind="card"
          items={tabs}
          activeKey={activeKey}
          onChange={setActiveKey}
        />
      </div>
    </div>
  );
}
