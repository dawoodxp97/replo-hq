'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import dynamic from 'next/dynamic';

// Dynamically import components to avoid SSR issues
const MarkdownRenderer = dynamic(() => import('./MarkdownRenderer'), { ssr: false });
const CodeSandbox = dynamic(() => import('./CodeSandbox'), { ssr: false });
const QuizComponent = dynamic(() => import('./QuizComponent'), { ssr: false });
const ProgressBar = dynamic(() => import('./ProgressBar'), { ssr: false });

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

interface TutorialPlayerProps {
  tutorialId: string;
}

const TutorialPlayer = ({ tutorialId }: TutorialPlayerProps) => {
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);
  const queryClient = useQueryClient();

  // Fetch tutorial data
  const { data: tutorial, isLoading, error } = useQuery<Tutorial>({
    queryKey: ['tutorial', tutorialId],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.TUTORIAL_GET_BY_ID(tutorialId));
    },
    enabled: !!tutorialId,
  });

  // Mutation for marking a module as complete
  const completeModuleMutation = useMutation({
    mutationFn: async (moduleId: string) => {
      return apiClient.post(API_ENDPOINTS.PROGRESS_COMPLETE_MODULE, { module_id: moduleId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progress'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !tutorial) {
    return (
      <div className="bg-red-50 p-4 rounded-lg text-red-700">
        Failed to load tutorial. Please try again later.
      </div>
    );
  }

  const currentModule = tutorial.modules[currentModuleIndex];
  const totalModules = tutorial.modules.length;
  const progress = ((currentModuleIndex + 1) / totalModules) * 100;

  const handlePrevious = () => {
    if (currentModuleIndex > 0) {
      setCurrentModuleIndex(currentModuleIndex - 1);
      setQuizCompleted(false);
    }
  };

  const handleNext = () => {
    // Mark current module as complete
    if (currentModule) {
      completeModuleMutation.mutate(currentModule.module_id);
    }

    // Move to next module if available
    if (currentModuleIndex < totalModules - 1) {
      setCurrentModuleIndex(currentModuleIndex + 1);
      setQuizCompleted(false);
      window.scrollTo(0, 0);
    }
  };

  const handleQuizComplete = (isCorrect: boolean) => {
    setQuizCompleted(true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tutorial header */}
      <div className="bg-white p-4 border-b">
        <h1 className="text-2xl font-bold">{tutorial.title}</h1>
        <div className="text-sm text-gray-600 mt-1">
          Level: <span className="font-medium">{tutorial.level}</span>
        </div>
      </div>

      {/* Progress bar */}
      <ProgressBar progress={progress} />

      {/* Main content area */}
      <div className="flex flex-col lg:flex-row flex-grow overflow-hidden">
        {/* Left pane: Tutorial content */}
        <div className="lg:w-1/2 p-6 overflow-y-auto">
          <h2 className="text-xl font-semibold mb-4">{currentModule.title}</h2>
          
          <MarkdownRenderer content={currentModule.content_markdown} />
          
          {/* Quiz section */}
          {currentModule.quiz && (
            <div className="mt-8 p-4 border rounded-lg bg-gray-50">
              <h3 className="text-lg font-medium mb-4">Quiz</h3>
              <QuizComponent 
                quiz={currentModule.quiz} 
                onComplete={handleQuizComplete} 
              />
            </div>
          )}
          
          {/* Navigation buttons */}
          <div className="mt-8 flex justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentModuleIndex === 0}
              className={`px-4 py-2 rounded ${
                currentModuleIndex === 0
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Previous
            </button>
            
            <button
              onClick={handleNext}
              disabled={!!(currentModule.quiz && !quizCompleted)}
              className={`px-4 py-2 rounded ${
                currentModule.quiz && !quizCompleted
                  ? 'bg-blue-300 text-white cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {currentModuleIndex === totalModules - 1 ? 'Finish' : 'Next'}
            </button>
          </div>
        </div>
        
        {/* Right pane: Code sandbox */}
        <div className="lg:w-1/2 border-t lg:border-t-0 lg:border-l">
          {currentModule.code_snippet ? (
            <CodeSandbox 
              code={currentModule.code_snippet} 
              filePath={currentModule.file_path || 'example.js'} 
            />
          ) : (
            <div className="flex justify-center items-center h-full bg-gray-100">
              <p className="text-gray-500">No code snippet available for this module.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TutorialPlayer;