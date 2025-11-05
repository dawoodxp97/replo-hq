'use client';

import { useEffect, useState } from 'react';
import { Card } from 'antd';
import { CheckCircle2, Circle, Plus, Save, Trash2 } from 'lucide-react';

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
      is_correct: i === index,
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
      options,
    });

    setIsDirty(false);
  };

  return (
    <Card
      className="border-0 shadow-lg bg-gradient-to-br from-white via-purple-50/30 to-pink-50/20 backdrop-blur-sm"
      bodyStyle={{ padding: '24px' }}
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Question Text */}
        <div className="space-y-2">
          <label
            htmlFor="question"
            className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
          >
            <span className="text-lg">❓</span>
            Question
          </label>
          <textarea
            id="question"
            value={questionText}
            onChange={e => {
              setQuestionText(e.target.value);
              setIsDirty(true);
            }}
            className="w-full px-4 py-3 border border-purple-200/50 rounded-xl bg-white/80 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 transition-all duration-200 shadow-sm hover:shadow-md resize-none"
            rows={3}
            required
            placeholder="Enter your question here..."
          />
        </div>

        {/* Options */}
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
            <span className="text-lg">📝</span>
            Answer Options
          </label>

          <div className="space-y-3">
            {options.map((option, index) => (
              <div
                key={index}
                className={`
                  flex items-center gap-3 p-4 rounded-xl border transition-all duration-200
                  ${
                    option.is_correct
                      ? 'bg-gradient-to-r from-green-50/80 via-emerald-50/60 to-teal-50/80 border-green-300/50 shadow-md'
                      : 'bg-white/80 backdrop-blur-sm border-purple-200/50 shadow-sm hover:shadow-md'
                  }
                `}
              >
                <button
                  type="button"
                  onClick={() => handleCorrectOptionChange(index)}
                  className={`
                    flex-shrink-0 p-1.5 rounded-full transition-all duration-200
                    ${
                      option.is_correct
                        ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg scale-110'
                        : 'bg-gray-200 hover:bg-gray-300 text-gray-400 hover:text-gray-600'
                    }
                  `}
                  title={
                    option.is_correct ? 'Correct answer' : 'Mark as correct'
                  }
                >
                  {option.is_correct ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <Circle className="w-5 h-5" />
                  )}
                </button>
                <input
                  type="text"
                  value={option.text}
                  onChange={e => handleOptionTextChange(index, e.target.value)}
                  className={`
                    flex-1 px-4 py-2 rounded-lg border transition-all duration-200
                    ${
                      option.is_correct
                        ? 'bg-white/90 border-green-300/50 focus:ring-2 focus:ring-green-400/50'
                        : 'bg-white/80 border-purple-200/50 focus:ring-2 focus:ring-purple-400/50'
                    }
                    focus:outline-none shadow-sm
                  `}
                  placeholder={`Option ${index + 1}`}
                  required
                />
                <button
                  type="button"
                  onClick={() => handleRemoveOption(index)}
                  disabled={options.length <= 2}
                  className={`
                    flex-shrink-0 p-2 rounded-lg transition-all duration-200
                    ${
                      options.length <= 2
                        ? 'text-gray-300 cursor-not-allowed opacity-50'
                        : 'text-red-500 hover:text-red-600 hover:bg-red-50 active:scale-95'
                    }
                  `}
                  title={
                    options.length <= 2
                      ? 'Minimum 2 options required'
                      : 'Remove option'
                  }
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>

          {/* Add Option Button */}
          <button
            type="button"
            onClick={handleAddOption}
            className="mt-3 w-full px-4 py-3 text-sm font-medium text-purple-600 hover:text-purple-700 bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 rounded-xl border border-purple-200/50 hover:border-purple-300 transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Option
          </button>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end pt-4 border-t border-purple-200/30">
          <button
            type="submit"
            disabled={isUpdating || !isDirty}
            className={`
              relative px-8 py-3 rounded-xl font-semibold text-white
              transition-all duration-300 transform
              ${
                isUpdating || !isDirty
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed opacity-60'
                  : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:via-purple-500 hover:to-pink-500 shadow-lg hover:shadow-xl hover:scale-105 active:scale-100'
              }
              overflow-hidden group
            `}
          >
            <span className="relative z-10 flex items-center gap-2">
              <Save className={`w-4 h-4 ${isUpdating ? 'animate-spin' : ''}`} />
              {isUpdating ? 'Saving...' : 'Save Quiz'}
            </span>
            {!isUpdating && isDirty && (
              <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></span>
            )}
          </button>
        </div>
      </form>
    </Card>
  );
};

export default QuizEditor;
