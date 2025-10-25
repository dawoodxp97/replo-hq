'use client';

import { useState, useEffect } from 'react';

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

interface QuizEditorProps {
  quiz: Quiz;
  onUpdate: (quizData: {
    question_text: string;
    options: QuizOption[];
  }) => void;
  isUpdating: boolean;
}

const QuizEditor = ({ quiz, onUpdate, isUpdating }: QuizEditorProps) => {
  const [questionText, setQuestionText] = useState(quiz.question_text);
  const [options, setOptions] = useState<QuizOption[]>(quiz.options);
  const [isDirty, setIsDirty] = useState(false);

  // Update state when quiz changes
  useEffect(() => {
    setQuestionText(quiz.question_text);
    setOptions(quiz.options);
    setIsDirty(false);
  }, [quiz]);

  const handleOptionTextChange = (index: number, text: string) => {
    const newOptions = [...options];
    newOptions[index] = { ...newOptions[index], text };
    setOptions(newOptions);
    setIsDirty(true);
  };

  const handleCorrectOptionChange = (index: number) => {
    const newOptions = options.map((option, i) => ({
      ...option,
      is_correct: i === index
    }));
    setOptions(newOptions);
    setIsDirty(true);
  };

  const handleAddOption = () => {
    setOptions([...options, { text: '', is_correct: false }]);
    setIsDirty(true);
  };

  const handleRemoveOption = (index: number) => {
    // Don't allow removing if there are only 2 options
    if (options.length <= 2) return;
    
    const newOptions = options.filter((_, i) => i !== index);
    
    // If we removed the correct option, make the first option correct
    if (options[index].is_correct && newOptions.length > 0) {
      newOptions[0] = { ...newOptions[0], is_correct: true };
    }
    
    setOptions(newOptions);
    setIsDirty(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Ensure at least one option is marked as correct
    const hasCorrectOption = options.some(option => option.is_correct);
    if (!hasCorrectOption && options.length > 0) {
      options[0] = { ...options[0], is_correct: true };
    }
    
    onUpdate({
      question_text: questionText,
      options
    });
    
    setIsDirty(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-gray-50 p-6 rounded-lg">
      {/* Question Text */}
      <div>
        <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-1">
          Question
        </label>
        <textarea
          id="question"
          value={questionText}
          onChange={(e) => {
            setQuestionText(e.target.value);
            setIsDirty(true);
          }}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          required
        />
      </div>
      
      {/* Options */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Answer Options
        </label>
        
        <div className="space-y-3">
          {options.map((option, index) => (
            <div key={index} className="flex items-center space-x-3">
              <input
                type="radio"
                id={`correct-${index}`}
                name="correct-option"
                checked={option.is_correct}
                onChange={() => handleCorrectOptionChange(index)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <input
                type="text"
                value={option.text}
                onChange={(e) => handleOptionTextChange(index, e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`Option ${index + 1}`}
                required
              />
              <button
                type="button"
                onClick={() => handleRemoveOption(index)}
                disabled={options.length <= 2}
                className={`p-2 rounded-md ${
                  options.length <= 2
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-red-600 hover:bg-red-100'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          ))}
        </div>
        
        {/* Add Option Button */}
        <button
          type="button"
          onClick={handleAddOption}
          className="mt-3 px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-md border border-blue-300"
        >
          + Add Option
        </button>
      </div>
      
      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isUpdating || !isDirty}
          className={`px-4 py-2 rounded-md ${
            isUpdating || !isDirty
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isUpdating ? 'Saving...' : 'Save Quiz'}
        </button>
      </div>
    </form>
  );
};

export default QuizEditor;