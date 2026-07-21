import { memo } from 'react';

interface LoaderProps {
  type?: 'spinner' | 'ai' | 'bar' | 'dots' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  message?: string;
}

const Loader = (props: LoaderProps) => {
  const {
    type = 'ai',
    size = 'md',
    className = '',
    message = 'Loading...',
  } = props;

  const sizeMap = {
    sm: {
      container: 'h-8 w-8',
      bar: 'h-1',
      dots: 'h-2 w-2',
      pulse: 'h-12 w-12',
      ai: 'h-16 w-16',
    },
    md: {
      container: 'h-12 w-12',
      bar: 'h-1.5',
      dots: 'h-3 w-3',
      pulse: 'h-16 w-16',
      ai: 'h-20 w-20',
    },
    lg: {
      container: 'h-16 w-16',
      bar: 'h-2',
      dots: 'h-4 w-4',
      pulse: 'h-24 w-24',
      ai: 'h-28 w-28',
    },
  };

  const renderLoader = () => {
    switch (type) {
      case 'spinner':
        return (
          <div className={`relative ${sizeMap[size].container}`}>
            <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 border-r-blue-500 animate-spin-slow"></div>
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-purple-500/20 animate-spin-slow-reverse blur-sm"></div>
          </div>
        );

      case 'ai':
        return (
          <div
            className={`relative ${sizeMap[size].ai} flex items-center justify-center`}
          >
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 opacity-60 animate-pulse-ai blur-xl"></div>
            <div className="absolute inset-2 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-blue-500 animate-pulse-soft"></div>
            <div className="absolute inset-4 rounded-full bg-gradient-to-tr from-purple-300 via-pink-300 to-blue-300 animate-pulse-inner"></div>
            <div className="absolute inset-6 rounded-full bg-white/80 backdrop-blur-sm animate-pulse-center"></div>
          </div>
        );

      case 'bar':
        return (
          <div className="w-48 space-y-2">
            <div
              className={`${sizeMap[size].bar} bg-gray-200 rounded-full overflow-hidden relative`}
            >
              <div className="absolute h-full w-1/3 bg-gradient-to-r from-purple-500 via-pink-500 to-blue-500 rounded-full animate-bar-progress"></div>
            </div>
            {size === 'lg' && (
              <div
                className={`${sizeMap[size].bar} bg-gray-200 rounded-full overflow-hidden relative`}
              >
                <div className="absolute h-full w-1/3 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full animate-bar-progress-delayed"></div>
              </div>
            )}
          </div>
        );

      case 'dots':
        return (
          <div className="flex items-center gap-2">
            <div
              className={`${sizeMap[size].dots} rounded-full bg-gradient-to-r from-purple-500 to-pink-500 animate-dot-bounce-1 shadow-lg shadow-purple-500/50`}
            ></div>
            <div
              className={`${sizeMap[size].dots} rounded-full bg-gradient-to-r from-pink-500 to-blue-500 animate-dot-bounce-2 shadow-lg shadow-pink-500/50`}
            ></div>
            <div
              className={`${sizeMap[size].dots} rounded-full bg-gradient-to-r from-blue-500 to-purple-500 animate-dot-bounce-3 shadow-lg shadow-blue-500/50`}
            ></div>
          </div>
        );

      case 'pulse':
        return (
          <div
            className={`relative ${sizeMap[size].pulse} flex items-center justify-center`}
          >
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-400 to-blue-400 opacity-40 animate-pulse-glow blur-2xl"></div>
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 animate-pulse-scale shadow-lg shadow-purple-500/50"></div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 ${className}`}
    >
      {renderLoader()}
      {message && (
        <p className="text-lg text-gray-600 dark:text-gray-400 font-medium animate-fade-in animate-text-shimmer">
          {message}
        </p>
      )}
    </div>
  );
};

export default memo(Loader);
