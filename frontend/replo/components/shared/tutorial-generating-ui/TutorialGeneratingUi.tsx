'use client';

import { memo } from 'react';
import { Progress, Steps } from 'antd';
import {
  Github,
  Sparkles,
  Code2,
  BookOpen,
  Zap,
  LucideIcon,
} from 'lucide-react';

interface TutorialGeneratingUiProps {
  generationStep: number;
  generationProgress: number;
}

const generationSteps = [
  { title: 'Cloning', icon: Github, description: 'Fetching repository...' },
  {
    title: 'Analyzing',
    icon: Code2,
    description: 'Parsing code structure...',
  },
  { title: 'Processing', icon: Zap, description: 'AI analyzing patterns...' },
  {
    title: 'Generating',
    icon: BookOpen,
    description: 'Creating tutorial...',
  },
];

const TutorialGeneratingUi = ({
  generationStep,
  generationProgress,
}: TutorialGeneratingUiProps) => {
  return (
    <div className="py-8">
      {/* AI-Themed Loading Animation */}
      <div className="flex flex-col items-center justify-center mb-8">
        <div className="relative mb-6">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 flex items-center justify-center shadow-2xl ai-pulse">
            <Sparkles className="w-12 h-12 text-white" />
          </div>
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 blur-xl opacity-50 animate-pulse"></div>
          <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-300 rounded-full animate-ping"></div>
          <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-purple-300 rounded-full animate-pulse"></div>
        </div>

        <div className="mb-6">
          <Steps
            current={Math.max(generationStep - 1, 0)}
            items={generationSteps.map(step => ({
              title: step.title,
              icon: <step.icon className="w-5 h-5" />,
            }))}
          />
        </div>
      </div>

      <div className="bg-gradient-to-br from-indigo-50/80 via-purple-50/80 to-pink-50/80 rounded-xl p-8 mb-6 border border-indigo-100/50 shadow-lg">
        <div className="flex items-center gap-4 mb-6">
          <div className="relative">
            <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center shadow-md ai-pulse">
              {(() => {
                const Icon: LucideIcon =
                  generationStep > 0 && generationStep <= generationSteps.length
                    ? generationSteps[generationStep - 1].icon
                    : Sparkles;
                return <Icon className="w-8 h-8 text-indigo-600" />;
              })()}
            </div>
            <div className="absolute inset-0 bg-indigo-200 rounded-xl blur-md opacity-30 animate-pulse"></div>
          </div>
          <div className="flex-1">
            <div className="text-lg font-semibold text-slate-900 mb-1">
              {generationStep > 0 && generationStep <= generationSteps.length
                ? generationSteps[generationStep - 1].title
                : 'Initializing AI...'}
            </div>
            <div className="text-sm text-slate-600">
              {generationStep > 0 && generationStep <= generationSteps.length
                ? generationSteps[generationStep - 1].description
                : 'Preparing AI models and analyzing repository...'}
            </div>
          </div>
        </div>

        <Progress
          percent={generationProgress}
          strokeColor={{
            '0%': '#818cf8',
            '50%': '#c084fc',
            '100%': '#f472b6',
          }}
          status="active"
          showInfo={false}
          className="mb-2"
        />
        <div className="flex justify-between text-xs text-slate-600">
          <span>Processing...</span>
          <span className="font-medium">{generationProgress}%</span>
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-center">
        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></div>
        <p className="text-sm text-slate-600">
          AI is crafting your tutorial. This may take a few moments...
        </p>
        <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-150"></div>
      </div>
    </div>
  );
};

export default memo(TutorialGeneratingUi);
