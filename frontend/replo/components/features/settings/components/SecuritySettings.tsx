import { Shield, Trash2, TriangleAlert } from 'lucide-react';
import {
  SettingsCard,
  SettingsContentWrapper,
  SettingsToggleCard,
} from '../layout/SettingsLayout';
import SaveSettingsChanges from './SaveSettingsChanges';
import { useState } from 'react';
import ReploInput from '@/components/ui/input/Input';
import { Button } from 'antd';

const SecuritySettings = () => {
  const [securitySettings, setSecuritySettings] = useState({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: '',
  });

  const handleOnChangeSecuritySettings = (key: string, value: any) => {
    setSecuritySettings((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleDeleteAccount = () => {
    console.log('Deleting account');
  };

  const handleSave = () => {
    console.log('Saving security settings', securitySettings);
  };
  return (
    <SettingsContentWrapper>
      <SettingsCard
        header={{
          icon: <Shield className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Password & Security',
          description: 'Manage your password and security settings',
        }}
      >
        <ReploInput
          title="Current Password"
          kind="password"
          value={securitySettings.currentPassword}
          onChange={(e, value) =>
            handleOnChangeSecuritySettings('currentPassword', value)
          }
          style={{ width: '100%' }}
        />
        <div className="mt-4"></div>
        <ReploInput
          title="New Password"
          kind="password"
          value={securitySettings.newPassword}
          onChange={(e, value) =>
            handleOnChangeSecuritySettings('newPassword', value)
          }
        />
        <div className="mt-4"></div>
        <ReploInput
          title="Confirm New Password"
          kind="password"
          value={securitySettings.confirmNewPassword}
          onChange={(e, value) =>
            handleOnChangeSecuritySettings('confirmNewPassword', value)
          }
        />
      </SettingsCard>
      <SettingsCard
        className="text-card-foreground flex flex-col rounded-xl border-2 border-red-100 shadow-lg hover:shadow-xl transition-shadow bg-gradient-to-br from-red-50/50 to-orange-50/50"
        header={{
          icon: <TriangleAlert className="w-5 h-5 text-red-600 mr-1" />,
          title: <span className="text-red-600">Danger Zone</span>,
          description: 'Irreversible actions for your account',
        }}
      >
        <SettingsToggleCard
          className="!h-auto flex items-center justify-between p-4 bg-white rounded-xl border-2 border-red-200"
          bgColor=""
          customButton={
            <Button
              type="primary"
              className="!bg-red-600 !hover:!bg-red-700"
              danger
              onClick={handleDeleteAccount}
            >
              <Trash2 className="w-4 h-4 mr-2 text-white" /> Delete
            </Button>
          }
          title="Delete Account"
          description="Permanently delete your account and all data"
          checked={false}
          onChange={() => {}}
        />
      </SettingsCard>
      <SaveSettingsChanges handleSave={handleSave} />
    </SettingsContentWrapper>
  );
};

export default SecuritySettings;
