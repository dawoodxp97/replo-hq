import { Palette } from 'lucide-react';
import { SettingsCard, SettingsContentWrapper } from '../layout/SettingsLayout';
import ReploInput from '@/components/ui/input/Input';
import { useState } from 'react';
import SaveSettingsChanges from './SaveSettingsChanges';

const AppearanceSettings = () => {
  const [appearanceSettings, setAppearanceSettings] = useState({
    language: 'en',
    theme: 'github-dark',
  });

  const handleLanguageChange = (value: string) => {
    setAppearanceSettings((prev: any) => ({ ...prev, language: value }));
  };

  const handleThemeChange = (value: string) => {
    setAppearanceSettings((prev: any) => ({ ...prev, theme: value }));
  };

  const handleSave = () => {
    console.log('Saving appearance settings');
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
