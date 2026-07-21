import { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Palette } from 'lucide-react';

import { SettingsCard, SettingsContentWrapper } from '../layout/SettingsLayout';

import SaveSettingsChanges from './SaveSettingsChanges';
import {
  AppearanceSettingsResponse,
  AppearanceSettingsUpdate,
  getUserAppearanceSettings,
  updateUserAppearanceSettings,
} from '@/services/settingsService';
import { snakeToCamel } from '@/utils/common';

import ReploInput from '@/components/ui/input/Input';
import Loader from '@/components/ui/loader/Loader';
import Error from '@/components/ui/error/Error';

const AppearanceSettings = () => {
  const [appearanceSettings, setAppearanceSettings] = useState({
    language: 'en',
    theme: 'github-dark',
  });
  const {
    data: appearanceSettingsData,
    isPending,
    isFetching,
    error: errorAppearanceSettings,
  } = useQuery({
    queryKey: ['appearanceSettings'],
    queryFn: async () => {
      const response = await getUserAppearanceSettings();
      const camelData = snakeToCamel(response);
      return camelData;
    },
    retry: false,
  });

  const updateAppearanceMutation = useMutation({
    mutationFn: async (appearanceSettings: AppearanceSettingsUpdate) => {
      return await updateUserAppearanceSettings({
        language: appearanceSettings.language,
        code_editor_theme: appearanceSettings.code_editor_theme,
      });
    },
    onSuccess: () => {
      toast.success('Appearance settings updated successfully!');
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail || 'Failed to update appearance settings'
      );
    },
  });

  useEffect(() => {
    if (appearanceSettingsData) {
      setAppearanceSettings({
        language: appearanceSettingsData.language,
        theme: appearanceSettingsData.codeEditorTheme,
      });
    }
  }, [appearanceSettingsData]);

  if (isPending || isFetching) {
    return (
      <Loader
        className="h-[300px] mt-25"
        type="ai"
        size="lg"
        message="Loading appearance settings..."
      />
    );
  }
  if (errorAppearanceSettings) {
    return (
      <Error
        title="Error loading appearance settings"
        variant="full"
        className="!h-[500px]"
        error={errorAppearanceSettings}
      />
    );
  }

  const handleLanguageChange = (value: string) => {
    setAppearanceSettings((prev: any) => ({ ...prev, language: value }));
  };

  const handleThemeChange = (value: string) => {
    setAppearanceSettings((prev: any) => ({ ...prev, theme: value }));
  };

  const handleSave = () => {
    updateAppearanceMutation.mutate({
      language: appearanceSettings.language,
      code_editor_theme: appearanceSettings.theme,
    });
  };
  return (
    <SettingsContentWrapper>
      <SettingsCard
        header={{
          icon: <Palette className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Appearance',
          description: 'Manage your appearance settings',
        }}
      >
        <ReploInput
          title="Language"
          kind="select"
          value={appearanceSettings.language}
          style={{ width: '100%' }}
          placeholder="Select a language"
          id="language-select"
          aria-label="Language select"
          aria-invalid={false}
          onChange={handleLanguageChange}
          options={[
            { label: 'English', value: 'en' },
            { label: 'Spanish', value: 'es' },
            { label: 'French', value: 'fr' },
          ]}
        />
        <div className="mt-4"></div>
        <ReploInput
          title="Code Editor Theme"
          kind="select"
          value={appearanceSettings.theme}
          style={{ width: '100%' }}
          placeholder="Select a theme"
          id="theme-select"
          aria-label="Theme select"
          aria-invalid={false}
          onChange={handleThemeChange}
          options={[
            { label: 'Light', value: 'light' },
            { label: 'Dark', value: 'dark' },
            { label: 'GitHub Dark', value: 'github-dark' },
            { label: 'GitHub Light', value: 'github-light' },
            { label: 'Dracula', value: 'dracula' },
            { label: 'Monokai', value: 'monokai' },
            { label: 'Nord', value: 'nord' },
          ]}
        />
      </SettingsCard>
      <SaveSettingsChanges handleSave={handleSave} />
    </SettingsContentWrapper>
  );
};

export default AppearanceSettings;
