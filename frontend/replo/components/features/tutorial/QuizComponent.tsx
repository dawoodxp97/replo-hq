'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import apiClient from '@/lib/apiClient';

interface QuizOption {
  text: string;
  is_correct: boolean;
}

interface Quiz {
  quiz_id: string;
  question_text: string;
  question_type: string;
  options: QuizOption[];
}

interface QuizComponentProps {
  quiz: Quiz;
  onComplete: (isCorrect: boolean) => void;
}

const QuizComponent = ({ quiz, onComplete }: QuizComponentProps) => {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | undefined>(undefined);

  const submitQuizMutation = useMutation({
    mutationFn: async ({
      quizId,
      answer,
    }: {
      quizId: string;
      answer: string;
    }) => {
      const response = await apiClient.post(
        API_ENDPOINTS.PROGRESS_SUBMIT_QUIZ,
        {
          quiz_id: quizId,
          submitted_answer: answer,
        }
      );
      return response as unknown as { is_correct: boolean };
    },
    onSuccess: (data: { is_correct: boolean }) => {
      setIsCorrect(data.is_correct);
      onComplete(data.is_correct);
    },
    onError: () => {
      setIsCorrect(false);
      onComplete(false);
    },
  });

  const handleOptionSelect = (optionText: string) => {
    if (!submitted) {
      setSelectedAnswer(optionText);
    }
  };

  const handleSubmit = () => {
    if (selectedAnswer) {
      setSubmitted(true);
      submitQuizMutation.mutate({
        quizId: quiz.quiz_id,
        answer: selectedAnswer,
      });
    }
  };

  return (
    <div className="quiz-component">
      <p className="font-medium mb-4">{quiz.question_text}</p>

      <div className="space-y-3 mb-6">
        {quiz.options.map((option, index) => (
          <div
            key={index}
            className={`group relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-300 ease-in-out transform ${
              selectedAnswer === option.text
                ? submitted
                  ? isCorrect
                    ? 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-400 shadow-lg shadow-emerald-100 scale-[1.02]'
                    : option.is_correct
                    ? 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-400 shadow-lg shadow-emerald-100 scale-[1.02]'
                    : 'bg-gradient-to-r from-red-50 to-rose-50 border-red-400 shadow-lg shadow-red-100 scale-[1.02]'
                  : 'bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border-blue-400 shadow-md shadow-blue-100 scale-[1.01]'
                : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-md hover:scale-[1.01] hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100'
            } ${submitted ? 'cursor-default' : ''}`}
            onClick={() => handleOptionSelect(option.text)}
          >
            <div className="flex items-center justify-between">
              <span
                className={`font-medium ${
                  selectedAnswer === option.text
                    ? submitted
                      ? isCorrect
                        ? 'text-emerald-700'
                        : option.is_correct
                        ? 'text-emerald-700'
                        : 'text-red-700'
                      : 'text-blue-700'
                    : 'text-gray-700'
                }`}
              >
                {option.text}
              </span>

              {submitted && selectedAnswer === option.text && (
                <span
                  className={`ml-3 flex items-center justify-center w-6 h-6 rounded-full font-bold text-sm transition-all duration-300 ${
                    option.is_correct
                      ? 'bg-emerald-500 text-white shadow-md shadow-emerald-200'
                      : 'bg-red-500 text-white shadow-md shadow-red-200'
                  }`}
                >
                  {option.is_correct ? '✓' : '✗'}
                </span>
              )}

              {submitted &&
                option.is_correct &&
                selectedAnswer !== option.text && (
                  <span className="ml-3 flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500 text-white font-bold text-sm shadow-md shadow-emerald-200 transition-all duration-300">
                    ✓
                  </span>
                )}
            </div>
          </div>
        ))}
      </div>

      {!submitted ? (
        <button
          onClick={handleSubmit}
          disabled={!selectedAnswer}
          className={`px-4 py-2 rounded ${
            !selectedAnswer
              ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 !text-white hover:bg-blue-700 cursor-pointer'
          }`}
        >
          Submit Answer
        </button>
      ) : (
        <div
          className={`p-4 rounded ${isCorrect ? 'bg-green-100' : 'bg-red-100'}`}
        >
          <p className="font-medium">
            {isCorrect
              ? 'Correct! Well done!'
              : 'Incorrect. Review the correct answer above.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default QuizComponent;
