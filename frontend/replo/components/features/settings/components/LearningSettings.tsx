import { Zap } from 'lucide-react';
import {
  SettingsCard,
  SettingsContentWrapper,
  SettingsSeparator,
  SettingsToggleCard,
} from '../layout/SettingsLayout';
import { useState } from 'react';
import ReploInput from '@/components/ui/input/Input';
import SaveSettingsChanges from './SaveSettingsChanges';

const LearningSettings = () => {
  const [learningSettings, setLearningSettings] = useState({
    defaultDifficultyLevel: 'beginner',
    dailyLearningGoal: 10,
    autoPlayNextModule: true,
    showCodeHints: true,
    quizMode: true,
  });

  const handleOnChangeLearningSettings = (key: string, value: any) => {
    setLearningSettings((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    console.log('Saving learning settings');
  };
  return (
    <SettingsContentWrapper>
      <SettingsCard
        header={{
          icon: <Zap className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Learning Preferences',
          description: 'Customize your learning experience',
        }}
      >
        <ReploInput
          title="Default Difficulty Level"
          kind="select"
          value={learningSettings.defaultDifficultyLevel}
          style={{ width: '100%' }}
          placeholder="Select a difficulty level"
          id="default-difficulty-level-select"
          aria-label="Default difficulty level select"
          aria-invalid={false}
          onChange={value =>
            handleOnChangeLearningSettings('defaultDifficultyLevel', value)
          }
          options={[
            { label: 'Beginner', value: 'beginner' },
            { label: 'Intermediate', value: 'intermediate' },
            { label: 'Advanced', value: 'advanced' },
          ]}
        />
        <div className="mt-4"></div>
        <ReploInput
          title="Daily Learning Goal"
          kind="number"
          value={learningSettings.dailyLearningGoal}
          style={{ width: '100%' }}
          placeholder="Enter your daily learning goal"
          id="daily-learning-goal-input"
          aria-label="Daily learning goal input"
          aria-invalid={false}
          onChange={value =>
            handleOnChangeLearningSettings('dailyLearningGoal', value)
          }
          min={1}
          step={1}
          responsive
        />
        <SettingsSeparator />
        <SettingsToggleCard
          bgColor=""
          title="Auto-play Next Module"
          description="Automatically start next module after completion"
          checked={learningSettings.autoPlayNextModule}
          onChange={value =>
            handleOnChangeLearningSettings('autoPlayNextModule', value)
          }
        />
        <SettingsToggleCard
          bgColor=""
          title="Show Code Hints"
          description="Display helpful hints in code editor"
          checked={learningSettings.showCodeHints}
          onChange={value =>
            handleOnChangeLearningSettings('showCodeHints', value)
          }
        />
        <SettingsToggleCard
          bgColor=""
          title="Quiz Mode"
          description="Require quiz completion to proceed"
          checked={learningSettings.quizMode}
          onChange={value => handleOnChangeLearningSettings('quizMode', value)}
        />
      </SettingsCard>
      <SaveSettingsChanges handleSave={handleSave} />
    </SettingsContentWrapper>
  );
};

export default LearningSettings;
