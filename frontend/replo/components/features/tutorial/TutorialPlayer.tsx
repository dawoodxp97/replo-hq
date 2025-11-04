'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import dynamic from 'next/dynamic';
import { Card, Tabs, Progress, Tag, Button } from 'antd';
import {
  BookOpen,
  Code2,
  CheckCircle2,
  Circle,
  ChevronRight,
  FileText,
  Lightbulb,
  HelpCircle,
  GitBranch,
  Sparkles,
  CircleDotDashed,
} from 'lucide-react';
import Loader from '@/components/ui/loader/Loader';
import Error from '@/components/ui/error/Error';

// Dynamically import components to avoid SSR issues
const MarkdownRenderer = dynamic(() => import('./MarkdownRenderer'), {
  ssr: false,
});
const CodeSandbox = dynamic(() => import('./CodeSandbox'), { ssr: false });
const QuizComponent = dynamic(() => import('./QuizComponent'), { ssr: false });
const DiagramViewer = dynamic(() => import('./DiagramViewer.jsx'), {
  ssr: false,
});

// Define types
interface Quiz {
  quiz_id: string;
  question_text: string;
  question_type: string;
  options: Array<{
    text: string;
    is_correct: boolean;
  }>;
}

interface Module {
  module_id: string;
  title: string;
  order_index: number;
  content_markdown: string;
  file_path: string | null;
  code_snippet: string | null;
  diagram_mermaid: string | null;
  quiz: Quiz | null;
}

interface Tutorial {
  tutorial_id: string;
  repo_id: string;
  level: string;
  title: string;
  overview: string | null;
  overview_diagram_mermaid: string | null;
  generated_at: string;
  modules: Module[];
  repo_name: string | null;
  repo_url: string | null;
}

interface UserProgress {
  user_id: string;
  progress: Array<{
    progress_id: string;
    module_id: string;
    completed_at: string;
    quiz_score: number | null;
  }>;
}

interface TutorialPlayerProps {
  tutorialId: string;
}

const TutorialPlayer = ({ tutorialId }: TutorialPlayerProps) => {
  const [selectedModuleIndex, setSelectedModuleIndex] = useState(0);
  const [activeTab, setActiveTab] = useState('explanation');
  const [quizCompleted, setQuizCompleted] = useState(false);
  const queryClient = useQueryClient();

  // Fetch tutorial data
  const {
    data: tutorial,
    isLoading,
    error,
  } = useQuery<Tutorial>({
    queryKey: ['tutorial', tutorialId],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.TUTORIAL_GET_BY_ID(tutorialId));
    },
    enabled: !!tutorialId,
  });

  // Fetch user progress to show completed modules
  const { data: userProgress } = useQuery<UserProgress>({
    queryKey: ['progress'],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.PROGRESS_GET);
    },
  });

  // Create a set of completed module IDs
  const completedModuleIds = useMemo(() => {
    if (!userProgress?.progress) return new Set<string>();
    return new Set(userProgress.progress.map(p => p.module_id));
  }, [userProgress]);

  // Calculate overall progress percentage
  const overallProgress = useMemo(() => {
    if (!tutorial?.modules.length) return 0;
    const completedCount = tutorial.modules.filter(m =>
      completedModuleIds.has(m.module_id)
    ).length;
    return Math.round((completedCount / tutorial.modules.length) * 100);
  }, [tutorial, completedModuleIds]);

  // Mutation for marking a module as complete
  const completeModuleMutation = useMutation({
    mutationFn: async (moduleId: string) => {
      return apiClient.post(API_ENDPOINTS.PROGRESS_COMPLETE_MODULE, {
        module_id: moduleId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progress'] });
    },
  });

  const getDifficultyColor = (level: string) => {
    const levelUpper = level.toUpperCase();
    if (levelUpper.includes('BEGINNER')) return 'green';
    if (levelUpper.includes('INTERMEDIATE')) return 'blue';
    if (levelUpper.includes('ADVANCED')) return 'purple';
    return 'default';
  };

  const getDifficultyLabel = (level: string) => {
    const levelUpper = level.toUpperCase();
    if (levelUpper.includes('BEGINNER')) return 'Beginner';
    if (levelUpper.includes('INTERMEDIATE')) return 'Intermediate';
    if (levelUpper.includes('ADVANCED')) return 'Advanced';
    return level;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader type="spinner" size="lg" />
      </div>
    );
  }

  if (error || !tutorial) {
    return (
      <Error
        title="Error loading tutorial"
        variant="full"
        message="Failed to load tutorial. Please try again later."
        error={error}
      />
    );
  }

  const currentModule = tutorial.modules[selectedModuleIndex];
  const totalModules = tutorial.modules.length;
  const isModuleCompleted = completedModuleIds.has(
    currentModule?.module_id || ''
  );

  const handlePrevious = () => {
    if (selectedModuleIndex > 0) {
      setSelectedModuleIndex(selectedModuleIndex - 1);
      setQuizCompleted(false);
      setActiveTab('explanation');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleNext = () => {
    // Mark current module as complete if not already completed
    if (currentModule && !isModuleCompleted) {
      completeModuleMutation.mutate(currentModule.module_id);
    }

    // Move to next module if available
    if (selectedModuleIndex < totalModules - 1) {
      setSelectedModuleIndex(selectedModuleIndex + 1);
      setQuizCompleted(false);
      setActiveTab('explanation');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleQuizComplete = (isCorrect: boolean) => {
    setQuizCompleted(true);
  };

  const handleModuleSelect = (index: number) => {
    setSelectedModuleIndex(index);
    setQuizCompleted(false);
    setActiveTab('explanation');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="max-w-[calc(100vw-220px)] pt-6 pb-4 h-[calc(100vh-90px)] overflow-auto">
      {/* Tutorial Header */}
      <Card className="bg-white/90 backdrop-blur-sm mb-6 shadow-[0px_7px_29px_rgba(100,100,111,0.15)] !ml-6 !mr-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <h1 className="text-2xl md:text-3xl font-semibold text-slate-900">
                {tutorial.title}
              </h1>
              <Tag
                color={getDifficultyColor(tutorial.level)}
                className="text-sm"
              >
                {getDifficultyLabel(tutorial.level)}
              </Tag>
            </div>
            {tutorial.repo_name && (
              <p className="text-slate-600 mb-4 text-sm md:text-base">
                {tutorial.repo_name}
              </p>
            )}

            <div className="max-w-md">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-600">Overall Progress</span>
                <span className="font-medium text-slate-900">
                  {overallProgress}%
                </span>
              </div>
              <Progress
                percent={overallProgress}
                strokeColor={{
                  '0%': '#6366f1',
                  '100%': '#a855f7',
                }}
                className="mb-0"
              />
            </div>
          </div>
        </div>
      </Card>

      <div className="w-full flex flex-col gap-6 overflow-auto justify-center mt-6 mb-6 pl-6 pr-6 backdrop-blur-sm">
        <Card
          title={
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-500" />
              <span className="font-semibold">Modules</span>
            </div>
          }
          className="bg-white/90 shadow-[0px_7px_29px_rgba(100,100,111,0.15)]"
        >
          <div className="flex flex-col gap-4">
            {tutorial.modules.map((module, index) => {
              const isCompleted = completedModuleIds.has(module.module_id);
              const isSelected = index === selectedModuleIndex;

              return (
                <button
                  key={module.module_id}
                  onClick={() => handleModuleSelect(index)}
                  className={`w-full text-left p-4 rounded-xl transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? 'bg-gradient-to-r from-indigo-50/80 via-purple-50/80 to-pink-50/80 border-2 border-indigo-200/50 shadow-sm'
                      : 'bg-slate-50 hover:bg-slate-100/80 border-2 border-transparent hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="mt-0.5">
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                      ) : (
                        <CircleDotDashed className="w-5 h-5 text-slate-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm text-slate-900 mb-1">
                        {module.title}
                      </div>
                      <div className="text-xs text-slate-600">
                        Module {module.order_index + 1}
                      </div>
                    </div>
                    {isSelected && (
                      <ChevronRight className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        <Card className="border-slate-200/50 bg-white/90 backdrop-blur-sm shadow-sm">
          {currentModule && (
            <>
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={[
                  {
                    key: 'explanation',
                    label: (
                      <span className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Explanation
                      </span>
                    ),
                    children: (
                      <div className="prose max-w-none">
                        <div className="bg-gradient-to-r from-indigo-50/80 via-purple-50/80 to-pink-50/80 rounded-xl p-5 mb-6 border border-indigo-100/50 shadow-sm">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-400 rounded-lg flex items-center justify-center flex-shrink-0 shadow-md">
                              <Lightbulb className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <h4 className="font-semibold text-slate-900 mb-2">
                                Learning Objectives
                              </h4>
                              <p className="text-sm text-slate-600 leading-relaxed">
                                By the end of this module, you'll understand{' '}
                                {currentModule.title.toLowerCase()}.
                              </p>
                            </div>
                          </div>
                        </div>
                        <MarkdownRenderer
                          content={currentModule.content_markdown}
                        />
                      </div>
                    ),
                  },
                  {
                    key: 'code',
                    label: (
                      <span className="flex items-center gap-2">
                        <Code2 className="w-4 h-4" />
                        Code Editor
                      </span>
                    ),
                    children: currentModule.code_snippet ? (
                      <div className="space-y-4">
                        <div className="bg-gradient-to-r from-amber-50/80 via-orange-50/80 to-yellow-50/80 rounded-xl p-5 border border-amber-200/50 shadow-sm mb-4">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-400 rounded-lg flex items-center justify-center flex-shrink-0 shadow-md">
                              <Code2 className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <h4 className="font-semibold text-slate-900 mb-2">
                                Try It Yourself
                              </h4>
                              <p className="text-sm text-slate-600 leading-relaxed">
                                Modify the code below and see the results in
                                real-time.
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="border border-slate-200 rounded-lg overflow-hidden">
                          <CodeSandbox
                            code={currentModule.code_snippet}
                            filePath={currentModule.file_path || 'example.js'}
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="flex justify-center items-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                        <p className="text-gray-500">
                          No code snippet available for this module.
                        </p>
                      </div>
                    ),
                  },
                  {
                    key: 'diagram',
                    label: (
                      <span className="flex items-center gap-2">
                        <GitBranch className="w-4 h-4" />
                        Diagram
                      </span>
                    ),
                    children: currentModule.diagram_mermaid ? (
                      <DiagramViewer diagram={currentModule.diagram_mermaid} />
                    ) : (
                      <div className="flex justify-center items-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                        <p className="text-gray-500">
                          No diagram available for this module.
                        </p>
                      </div>
                    ),
                  },
                  ...(currentModule.quiz
                    ? [
                        {
                          key: 'quiz',
                          label: (
                            <span className="flex items-center gap-2">
                              <HelpCircle className="w-4 h-4" />
                              Quiz
                            </span>
                          ),
                          children: (
                            <div className="space-y-4">
                              <div className="bg-gradient-to-r from-blue-50/80 via-cyan-50/80 to-teal-50/80 rounded-xl p-5 border border-blue-200/50 shadow-sm mb-4">
                                <div className="flex items-start gap-3">
                                  <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-lg flex items-center justify-center flex-shrink-0 shadow-md">
                                    <HelpCircle className="w-5 h-5 text-white" />
                                  </div>
                                  <div>
                                    <h4 className="font-semibold text-slate-900 mb-2">
                                      Test Your Knowledge
                                    </h4>
                                    <p className="text-sm text-slate-600 leading-relaxed">
                                      Answer the question below to verify your
                                      understanding.
                                    </p>
                                  </div>
                                </div>
                              </div>
                              <QuizComponent
                                quiz={currentModule.quiz}
                                onComplete={handleQuizComplete}
                              />
                            </div>
                          ),
                        },
                      ]
                    : []),
                ]}
              />

              <div className="flex justify-between mt-6 pt-6 border-t border-slate-200">
                <Button
                  size="large"
                  onClick={handlePrevious}
                  disabled={selectedModuleIndex === 0}
                >
                  Previous Module
                </Button>
                <Button
                  type="primary"
                  size="large"
                  onClick={handleNext}
                  disabled={
                    !!(
                      currentModule.quiz &&
                      !quizCompleted &&
                      selectedModuleIndex < totalModules - 1
                    )
                  }
                  className="bg-gradient-to-r from-indigo-500 to-purple-500 border-0 hover:from-indigo-600 hover:to-purple-600"
                >
                  {selectedModuleIndex === totalModules - 1
                    ? 'Finish'
                    : 'Next Module'}
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
};

export default TutorialPlayer;
