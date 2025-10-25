'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';

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

  // Mutation for submitting quiz answer
  const submitQuizMutation = useMutation({
    mutationFn: async ({ quizId, answer }: { quizId: string; answer: string }) => {
      const response = await apiClient.post(API_ENDPOINTS.PROGRESS_SUBMIT_QUIZ, {
        quiz_id: quizId,
        submitted_answer: answer,
      });
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
      
      <div className="space-y-2 mb-6">
        {quiz.options.map((option, index) => (
          <div
            key={index}
            className={`p-3 border rounded cursor-pointer ${
              selectedAnswer === option.text
                ? submitted
                  ? isCorrect
                    ? 'bg-green-100 border-green-500'
                    : option.is_correct
                    ? 'bg-green-100 border-green-500'
                    : 'bg-red-100 border-red-500'
                  : 'bg-blue-50 border-blue-500'
                : 'hover:bg-gray-100'
            }`}
            onClick={() => handleOptionSelect(option.text)}
          >
            {option.text}
            
            {submitted && selectedAnswer === option.text && (
              <span className="float-right">
                {option.is_correct ? '✓' : '✗'}
              </span>
            )}
            
            {submitted && option.is_correct && selectedAnswer !== option.text && (
              <span className="float-right text-green-600">✓</span>
            )}
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
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          Submit Answer
        </button>
      ) : (
        <div className={`p-4 rounded ${isCorrect ? 'bg-green-100' : 'bg-red-100'}`}>
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