'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import dynamic from 'next/dynamic';
import Loader from '../ui/loader/Loader';
import Error from '../ui/error/Error';

const ModuleEditor = dynamic(() => import('./ModuleEditor'), { ssr: false });
const QuizEditor = dynamic(() => import('./QuizEditor'), { ssr: false });

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
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader type="spinner" size="lg" />
        <p className="text-lg text-gray-600">Loading tutorial...</p>
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

  const currentModule = tutorial.modules[selectedModuleIndex];

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

  return (
    <div className="flex h-full">
      {/* Left sidebar - Module list */}
      <div className="w-64 bg-gray-100 p-4 overflow-y-auto border-r">
        <h2 className="text-lg font-semibold mb-4">{tutorial.title}</h2>
        <p className="text-sm text-gray-600 mb-4">Level: {tutorial.level}</p>

        <h3 className="font-medium mb-2">Modules</h3>
        <ul className="space-y-1">
          {tutorial.modules.map((module, index) => (
            <li key={module.module_id}>
              <button
                onClick={() => setSelectedModuleIndex(index)}
                className={`w-full text-left px-3 py-2 rounded text-sm ${
                  index === selectedModuleIndex
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'hover:bg-gray-200'
                }`}
              >
                {index + 1}. {module.title}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-6">Edit Module</h2>

          {/* Module editor */}
          <ModuleEditor
            module={currentModule}
            onUpdate={handleModuleUpdate}
            isUpdating={updateModuleMutation.isPending}
          />

          {/* Quiz editor */}
          {currentModule.quiz && (
            <div className="mt-8">
              <h3 className="text-xl font-semibold mb-4">Edit Quiz</h3>
              <QuizEditor
                quiz={currentModule.quiz}
                onUpdate={handleQuizUpdate}
                isUpdating={updateQuizMutation.isPending}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TutorialEditor;
