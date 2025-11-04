'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Input, Select, Button, message, Tabs } from 'antd';
import { Editor } from '@monaco-editor/react';
import {
  ArrowUp,
  ArrowDown,
  Save,
  Settings,
  FileText,
  Sparkles,
} from 'lucide-react';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import dynamic from 'next/dynamic';
import Loader from '../ui/loader/Loader';
import Error from '../ui/error/Error';

const ModuleEditor = dynamic(() => import('./ModuleEditor'), { ssr: false });
const QuizEditor = dynamic(() => import('./QuizEditor'), { ssr: false });
const { TextArea } = Input;

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
}

interface TutorialEditorProps {
  tutorialId: string;
}

const TutorialEditor = ({ tutorialId }: TutorialEditorProps) => {
  const [selectedModuleIndex, setSelectedModuleIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<'modules' | 'settings'>('modules');
  const [tutorialMetadata, setTutorialMetadata] = useState({
    title: '',
    overview: '',
    level: '',
    overview_diagram_mermaid: '',
  });
  const [isMetadataDirty, setIsMetadataDirty] = useState(false);
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

  // Update metadata when tutorial data loads
  useEffect(() => {
    if (tutorial) {
      setTutorialMetadata({
        title: tutorial.title,
        overview: tutorial.overview || '',
        level: tutorial.level,
        overview_diagram_mermaid: tutorial.overview_diagram_mermaid || '',
      });
      setIsMetadataDirty(false);
    }
  }, [tutorial]);

  // Ensure selectedModuleIndex is valid when tutorial loads
  // This hook must be called before any conditional returns
  useEffect(() => {
    if (tutorial && tutorial.modules && tutorial.modules.length > 0) {
      if (selectedModuleIndex >= tutorial.modules.length) {
        setSelectedModuleIndex(0);
      }
    }
  }, [tutorial, selectedModuleIndex]);

  // Mutation for updating tutorial metadata
  const updateTutorialMutation = useMutation({
    mutationFn: async (data: {
      title?: string;
      overview?: string;
      level?: string;
      overview_diagram_mermaid?: string;
    }) => {
      return apiClient.put(
        API_ENDPOINTS.AUTHOR_UPDATE_TUTORIAL(tutorialId),
        data
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorial', tutorialId] });
      setIsMetadataDirty(false);
      message.success('Tutorial metadata updated successfully');
    },
    onError: () => {
      message.error('Failed to update tutorial metadata');
    },
  });

  // Mutation for reordering modules
  const reorderModulesMutation = useMutation({
    mutationFn: async (moduleIds: string[]) => {
      return apiClient.put(API_ENDPOINTS.AUTHOR_REORDER_MODULES(tutorialId), {
        module_ids: moduleIds,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorial', tutorialId] });
      message.success('Modules reordered successfully');
    },
    onError: () => {
      message.error('Failed to reorder modules');
    },
  });

  // Mutation for updating a module
  const updateModuleMutation = useMutation({
    mutationFn: async (moduleData: {
      moduleId: string;
      title: string;
      content_markdown: string;
      code_snippet: string;
      diagram_mermaid?: string;
    }) => {
      return apiClient.put(
        API_ENDPOINTS.AUTHOR_UPDATE_MODULE(moduleData.moduleId),
        {
          title: moduleData.title,
          content_markdown: moduleData.content_markdown,
          code_snippet: moduleData.code_snippet,
          diagram_mermaid: moduleData.diagram_mermaid,
        }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorial', tutorialId] });
      message.success('Module updated successfully');
    },
    onError: () => {
      message.error('Failed to update module');
    },
  });

  // Mutation for updating a quiz
  const updateQuizMutation = useMutation({
    mutationFn: async (quizData: {
      quizId: string;
      question_text: string;
      options: Array<{ text: string; is_correct: boolean }>;
    }) => {
      return apiClient.put(API_ENDPOINTS.AUTHOR_UPDATE_QUIZ(quizData.quizId), {
        question_text: quizData.question_text,
        options: quizData.options,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutorial', tutorialId] });
      message.success('Quiz updated successfully');
    },
    onError: () => {
      message.error('Failed to update quiz');
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center h-full bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-pink-50/20">
        <Loader type="ai" size="lg" />
        <p className="text-lg text-gray-600 mt-4 font-medium">
          Loading tutorial...
        </p>
      </div>
    );
  }

  if (error || !tutorial) {
    return (
      <Error
        variant="full"
        title="Error loading tutorial"
        message="Failed to load tutorial. Please try again later."
        error={error}
      />
    );
  }

  if (!tutorial || !tutorial.modules || tutorial.modules.length === 0) {
    return (
      <div className="flex justify-center items-center h-full bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-pink-50/20">
        <div className="text-center p-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-indigo-200/50">
          <Sparkles className="w-16 h-16 text-indigo-400 mx-auto mb-4" />
          <p className="text-lg text-gray-600 font-medium">
            No modules found in this tutorial.
          </p>
        </div>
      </div>
    );
  }

  const currentModule = tutorial.modules[selectedModuleIndex];

  const handleMetadataChange = (field: string, value: string) => {
    setTutorialMetadata(prev => ({ ...prev, [field]: value }));
    setIsMetadataDirty(true);
  };

  const handleMetadataSave = () => {
    updateTutorialMutation.mutate({
      title: tutorialMetadata.title,
      overview: tutorialMetadata.overview || undefined,
      level: tutorialMetadata.level,
      overview_diagram_mermaid:
        tutorialMetadata.overview_diagram_mermaid || undefined,
    });
  };

  const handleModuleMove = (index: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === tutorial.modules.length - 1)
    ) {
      return;
    }

    const newModules = [...tutorial.modules];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newModules[index], newModules[targetIndex]] = [
      newModules[targetIndex],
      newModules[index],
    ];

    const moduleIds = newModules.map(m => m.module_id);
    reorderModulesMutation.mutate(moduleIds);

    // Update selected index if needed
    if (selectedModuleIndex === index) {
      setSelectedModuleIndex(targetIndex);
    } else if (selectedModuleIndex === targetIndex) {
      setSelectedModuleIndex(index);
    }
  };

  const handleModuleUpdate = (moduleData: {
    title: string;
    content_markdown: string;
    code_snippet: string;
    diagram_mermaid?: string;
  }) => {
    updateModuleMutation.mutate({
      moduleId: currentModule.module_id,
      ...moduleData,
    });
  };

  const handleQuizUpdate = (quizData: {
    question_text: string;
    options: Array<{ text: string; is_correct: boolean }>;
  }) => {
    if (currentModule.quiz) {
      updateQuizMutation.mutate({
        quizId: currentModule.quiz.quiz_id,
        ...quizData,
      });
    }
  };

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      BEGINNER: 'from-green-500 to-emerald-500',
      INTERMEDIATE: 'from-blue-500 to-indigo-500',
      ADVANCED: 'from-purple-500 to-pink-500',
    };
    return colors[level.toUpperCase()] || 'from-gray-500 to-gray-600';
  };

  return (
    <div className="flex h-full bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-pink-50/20">
      {/* Left sidebar - Module list */}
      <div className="w-72 bg-white/80 backdrop-blur-xl border-r border-indigo-200/50 shadow-xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-indigo-200/50 bg-gradient-to-br from-indigo-50/50 to-purple-50/30">
          <div className="flex items-center gap-2">
            <div className="w-15 h-10 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg !mb-0 font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                {tutorial.title}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`px-2 py-0.5 text-xs font-semibold rounded-lg bg-gradient-to-r ${getLevelColor(
                    tutorial.level
                  )} text-white shadow-sm`}
                >
                  {tutorial.level}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex-1 overflow-hidden">
          <Tabs
            activeKey={activeTab}
            onChange={key => setActiveTab(key as 'modules' | 'settings')}
            items={[
              {
                key: 'modules',
                label: (
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Modules
                  </span>
                ),
                children: (
                  <div className="p-2 overflow-y-auto h-full">
                    <h3 className="font-semibold mb-3 text-sm text-gray-700 flex items-center justify-between">
                      <span>Modules ({tutorial.modules.length})</span>
                    </h3>
                    <ul className="space-y-2">
                      {tutorial.modules.map((module, index) => (
                        <li key={module.module_id} className="group">
                          <div
                            onClick={() => setSelectedModuleIndex(index)}
                            className={`
                            flex items-center gap-2 p-3 rounded-xl border transition-all duration-200 cursor-pointer
                            ${
                              index === selectedModuleIndex
                                ? 'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white shadow-lg scale-105 border-transparent'
                                : 'bg-white/80 backdrop-blur-sm border-indigo-200/50 hover:border-indigo-300 hover:shadow-md hover:bg-indigo-50/50'
                            }
                          `}
                          >
                            <button className="flex-1 text-left cursor-pointer">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`
                                  w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold
                                  ${
                                    index === selectedModuleIndex
                                      ? 'bg-white/20 text-white'
                                      : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
                                  }
                                `}
                                >
                                  {index + 1}
                                </span>
                                <span
                                  className={`text-sm font-medium line-clamp-1 ${
                                    index === selectedModuleIndex
                                      ? 'text-white'
                                      : 'text-gray-700'
                                  }`}
                                >
                                  {module.title}
                                </span>
                              </div>
                            </button>
                            <div className="flex flex-col gap-1">
                              <button
                                onClick={e => {
                                  e?.stopPropagation();
                                  e?.preventDefault();
                                  handleModuleMove(index, 'up');
                                }}
                                disabled={
                                  index === 0 ||
                                  reorderModulesMutation.isPending
                                }
                                className={`
                                  p-1.5 rounded-lg transition-all duration-200 cursor-pointer
                                  ${
                                    index === selectedModuleIndex
                                      ? 'bg-white/20 hover:bg-white/30 text-white'
                                      : 'bg-indigo-100 hover:bg-indigo-200 text-indigo-600'
                                  }
                                  disabled:opacity-30 disabled:cursor-not-allowed
                                `}
                                title="Move up"
                              >
                                <ArrowUp className="w-3 h-3" />
                              </button>
                              <button
                                onClick={e => {
                                  e?.stopPropagation();
                                  e?.preventDefault();
                                  handleModuleMove(index, 'down');
                                }}
                                disabled={
                                  index === tutorial.modules.length - 1 ||
                                  reorderModulesMutation.isPending
                                }
                                className={`
                                  p-1.5 rounded-lg transition-all duration-200 cursor-pointer
                                  ${
                                    index === selectedModuleIndex
                                      ? 'bg-white/20 hover:bg-white/30 text-white'
                                      : 'bg-indigo-100 hover:bg-indigo-200 text-indigo-600'
                                  }
                                  disabled:opacity-30 disabled:cursor-not-allowed
                                `}
                                title="Move down"
                              >
                                <ArrowDown className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ),
              },
              {
                key: 'settings',
                label: (
                  <span className="flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Settings
                  </span>
                ),
                children: (
                  <div className="p-4 overflow-y-auto h-full">
                    <div className="bg-gradient-to-br from-indigo-50/50 to-purple-50/30 rounded-xl p-4 border border-indigo-200/50">
                      <div className="flex items-center gap-2 mb-3">
                        <Settings className="w-5 h-5 text-indigo-500" />
                        <h3 className="font-semibold text-sm text-gray-700">
                          Tutorial Settings
                        </h3>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        Use the main content area to edit tutorial metadata,
                        including title, level, overview, and Mermaid diagrams.
                      </p>
                      <div className="mt-4 pt-4 border-t border-indigo-200/50">
                        <div className="space-y-2 text-xs">
                          <div className="flex items-center gap-2 text-gray-600">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                            <span>Edit tutorial title & overview</span>
                          </div>
                          <div className="flex items-center gap-2 text-gray-600">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                            <span>Change difficulty level</span>
                          </div>
                          <div className="flex items-center gap-2 text-gray-600">
                            <span className="w-1.5 h-1.5 rounded-full bg-pink-400"></span>
                            <span>Update Mermaid diagrams</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ),
              },
            ]}
            className="h-full !p-2"
          />
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {activeTab === 'modules' && (
            <>
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-indigo-200/50 p-6">
                <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-2">
                  <FileText className="w-6 h-6 text-indigo-500" />
                  Edit Module
                </h2>

                {/* Module editor */}
                <ModuleEditor
                  module={currentModule}
                  onUpdate={handleModuleUpdate}
                  isUpdating={updateModuleMutation.isPending}
                />
              </div>

              {/* Quiz editor */}
              {currentModule.quiz && (
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-indigo-200/50 p-6">
                  <h3 className="text-xl font-semibold mb-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-2">
                    <span className="text-2xl">🎯</span>
                    Edit Quiz
                  </h3>
                  <QuizEditor
                    quiz={currentModule.quiz}
                    onUpdate={handleQuizUpdate}
                    isUpdating={updateQuizMutation.isPending}
                  />
                </div>
              )}
            </>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6 flex flex-col gap-4">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-indigo-200/50 p-6 flex flex-col gap-4">
                <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent flex items-center gap-2">
                  <Settings className="w-6 h-6 text-indigo-500" />
                  Tutorial Settings
                </h2>

                <Card
                  title={
                    <span className="font-semibold text-gray-700">
                      Basic Information
                    </span>
                  }
                  className="border-0 shadow-lg bg-gradient-to-br from-white via-indigo-50/30 to-purple-50/20 mb-6"
                  bodyStyle={{ padding: '24px' }}
                >
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Tutorial Title
                      </label>
                      <Input
                        value={tutorialMetadata.title}
                        onChange={e =>
                          handleMetadataChange('title', e.target.value)
                        }
                        placeholder="Tutorial title"
                        size="large"
                        className="rounded-xl border-indigo-200/50 focus:border-indigo-400"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Difficulty Level
                      </label>
                      <Select
                        value={tutorialMetadata.level}
                        onChange={value => handleMetadataChange('level', value)}
                        size="large"
                        className="w-full rounded-xl"
                      >
                        <Select.Option value="BEGINNER">Beginner</Select.Option>
                        <Select.Option value="INTERMEDIATE">
                          Intermediate
                        </Select.Option>
                        <Select.Option value="ADVANCED">Advanced</Select.Option>
                      </Select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Overview
                      </label>
                      <TextArea
                        value={tutorialMetadata.overview}
                        onChange={e =>
                          handleMetadataChange('overview', e.target.value)
                        }
                        placeholder="Tutorial overview and description"
                        rows={5}
                        size="large"
                        className="rounded-xl border-indigo-200/50 focus:border-indigo-400"
                      />
                    </div>
                  </div>
                </Card>

                <Card
                  title={
                    <span className="font-semibold text-gray-700">
                      Overview Diagram (Mermaid)
                    </span>
                  }
                  className="border-0 shadow-lg bg-gradient-to-br from-white via-indigo-50/30 to-purple-50/20"
                  bodyStyle={{ padding: '24px' }}
                >
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Mermaid Diagram Code
                    </label>
                    <div className="border border-indigo-200/50 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200 bg-white/90 backdrop-blur-sm">
                      <Editor
                        height="300px"
                        language="markdown"
                        value={tutorialMetadata.overview_diagram_mermaid}
                        onChange={value =>
                          handleMetadataChange(
                            'overview_diagram_mermaid',
                            value || ''
                          )
                        }
                        options={{
                          minimap: { enabled: false },
                          scrollBeyondLastLine: false,
                          wordWrap: 'on',
                          fontSize: 14,
                          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                        }}
                        theme="vs"
                      />
                    </div>
                  </div>
                </Card>

                <div className="flex justify-end pt-4">
                  <Button
                    type="primary"
                    size="large"
                    icon={<Save className="w-4 h-4" />}
                    onClick={handleMetadataSave}
                    disabled={
                      !isMetadataDirty || updateTutorialMutation.isPending
                    }
                    className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 border-0 hover:from-indigo-500 hover:via-purple-500 hover:to-pink-500 shadow-lg hover:shadow-xl"
                  >
                    {updateTutorialMutation.isPending
                      ? 'Saving...'
                      : 'Save Changes'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TutorialEditor;
