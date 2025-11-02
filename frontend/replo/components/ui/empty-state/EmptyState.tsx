import { memo } from 'react';

export type EmptyStateVariant =
  | 'illustration'
  | 'compact'
  | 'search'
  | 'table'
  | 'card';
export type EmptyStateSize = 'sm' | 'md' | 'lg';

export interface EmptyStateAction {
  label: string;
  onClick: () => void;
}

export interface EmptyStateProps {
  variant?: EmptyStateVariant;
  title?: string;
  description?: string;
  primaryAction?: EmptyStateAction;
  secondaryAction?: EmptyStateAction;
  illustration?: React.ReactNode;
  className?: string;
  showSuggestions?: boolean;
  suggestions?: string[];
  size?: EmptyStateSize;
}

const DefaultAIBlobIllustration = () => (
  <svg
    width="240"
    height="200"
    viewBox="0 0 240 200"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="animate-empty-float"
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="blobGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#E0E7FF" stopOpacity="0.8" />
        <stop offset="50%" stopColor="#F3E8FF" stopOpacity="0.6" />
        <stop offset="100%" stopColor="#FCE7F3" stopOpacity="0.4" />
      </linearGradient>
      <linearGradient id="blobGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#DBEAFE" stopOpacity="0.7" />
        <stop offset="100%" stopColor="#E0E7FF" stopOpacity="0.5" />
      </linearGradient>
      <filter id="glow">
        <feGaussianBlur stdDeviation="4" result="coloredBlur" />
        <feMerge>
          <feMergeNode in="coloredBlur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
    {/* Main blob */}
    <path
      d="M120 40C140 30, 170 35, 185 55C200 75, 195 105, 180 125C165 145, 135 155, 115 150C95 145, 80 130, 70 110C60 90, 65 65, 80 50C95 35, 100 50, 120 40Z"
      fill="url(#blobGrad1)"
      className="animate-empty-pulse"
      filter="url(#glow)"
    />
    {/* Secondary blob */}
    <path
      d="M80 90C85 75, 100 70, 115 75C130 80, 140 95, 135 110C130 125, 115 130, 100 125C85 120, 75 105, 80 90Z"
      fill="url(#blobGrad2)"
      className="animate-empty-float-delayed"
    />
    {/* Accent dots */}
    <circle
      cx="160"
      cy="80"
      r="6"
      fill="#C7D2FE"
      opacity="0.6"
      className="animate-empty-dot-1"
    />
    <circle
      cx="60"
      cy="120"
      r="5"
      fill="#DDD6FE"
      opacity="0.5"
      className="animate-empty-dot-2"
    />
    <circle
      cx="170"
      cy="140"
      r="4"
      fill="#E9D5FF"
      opacity="0.7"
      className="animate-empty-dot-3"
    />
  </svg>
);

const DefaultEmptyBoxIllustration = () => (
  <svg
    width="200"
    height="180"
    viewBox="0 0 200 180"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="animate-empty-float"
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="boxGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#F3F4F6" stopOpacity="0.9" />
        <stop offset="100%" stopColor="#E5E7EB" stopOpacity="0.7" />
      </linearGradient>
      <linearGradient id="boxGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#F9FAFB" stopOpacity="0.8" />
        <stop offset="100%" stopColor="#F3F4F6" stopOpacity="0.6" />
      </linearGradient>
    </defs>
    {/* Box base */}
    <rect
      x="40"
      y="80"
      width="120"
      height="80"
      rx="8"
      fill="url(#boxGrad1)"
      stroke="#D1D5DB"
      strokeWidth="2"
      className="animate-empty-pulse"
    />
    {/* Box lid */}
    <rect
      x="35"
      y="75"
      width="120"
      height="12"
      rx="6"
      fill="url(#boxGrad2)"
      stroke="#D1D5DB"
      strokeWidth="2"
    />
    {/* Empty indicator lines */}
    <line
      x1="70"
      y1="110"
      x2="130"
      y2="110"
      stroke="#CBD5E1"
      strokeWidth="2"
      strokeDasharray="4 4"
      opacity="0.6"
      className="animate-empty-fade"
    />
    <line
      x1="70"
      y1="125"
      x2="130"
      y2="125"
      stroke="#CBD5E1"
      strokeWidth="2"
      strokeDasharray="4 4"
      opacity="0.6"
      className="animate-empty-fade-delayed"
    />
  </svg>
);

const CompactIcon = ({ size }: { size: EmptyStateSize }) => {
  const iconSize = size === 'sm' ? 32 : size === 'md' ? 40 : 48;
  return (
    <svg
      width={iconSize}
      height={iconSize}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="text-gray-400"
    >
      <circle
        cx="20"
        cy="20"
        r="18"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        opacity="0.3"
      />
      <path
        d="M12 20H28M20 12V28"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.5"
      />
    </svg>
  );
};

const EmptyState = ({
  variant = 'illustration',
  title,
  description,
  primaryAction,
  secondaryAction,
  illustration,
  className = '',
  showSuggestions = false,
  suggestions = [],
  size = 'md',
}: EmptyStateProps) => {
  const defaultTitle = {
    illustration: 'No Data Available',
    compact: 'No Items',
    search: 'No Results Found',
    table: 'No Data',
    card: 'Empty',
  }[variant];

  const defaultDescription = {
    illustration: 'Get started by adding your first item.',
    compact: 'This list is empty.',
    search: 'Try adjusting your search terms or filters.',
    table: 'No rows match your current filters.',
    card: 'Add content to get started.',
  }[variant];

  const finalTitle = title || defaultTitle;
  const finalDescription = description || defaultDescription;

  const sizeClasses = {
    sm: {
      container: 'py-8 px-4',
      title: 'text-base',
      description: 'text-sm',
      illustration: 'w-32 h-28',
      icon: 'w-8 h-8',
      action: 'text-sm px-3 py-1.5',
    },
    md: {
      container: 'py-12 px-6',
      title: 'text-lg',
      description: 'text-base',
      illustration: 'w-48 h-40',
      icon: 'w-10 h-10',
      action: 'text-sm px-4 py-2',
    },
    lg: {
      container: 'py-16 px-8',
      title: 'text-xl',
      description: 'text-lg',
      illustration: 'w-60 h-52',
      icon: 'w-12 h-12',
      action: 'text-base px-5 py-2.5',
    },
  };

  const currentSize = sizeClasses[size];

  if (variant === 'compact') {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`flex items-center gap-3 text-center ${currentSize.container} ${className}`}
      >
        <div className="flex-shrink-0 text-gray-400">
          <CompactIcon size={size} />
        </div>
        <div className="flex-1 text-left min-w-0">
          <h3 className={`font-medium text-blue-700 ${currentSize.title}`}>
            {finalTitle}
          </h3>
          {finalDescription && (
            <p className={`text-gray-500 mt-1 ${currentSize.description}`}>
              {finalDescription}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (variant === 'search') {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`flex flex-col items-center justify-center text-center ${currentSize.container} ${className}`}
      >
        <div className="relative mb-6">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-100/40 via-purple-100/30 to-pink-100/40 rounded-full blur-2xl animate-empty-glow" />
          <div className="relative">
            <svg
              width="120"
              height="120"
              viewBox="0 0 120 120"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="animate-empty-float"
              aria-hidden="true"
            >
              <circle
                cx="60"
                cy="60"
                r="50"
                stroke="url(#searchGrad)"
                strokeWidth="3"
                fill="none"
                opacity="0.3"
              />
              <defs>
                <linearGradient
                  id="searchGrad"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stopColor="#93C5FD" />
                  <stop offset="100%" stopColor="#C7D2FE" />
                </linearGradient>
              </defs>
              <path
                d="M75 75L95 95M60 45C52.27 45 46 51.27 46 59C46 66.73 52.27 73 60 73C67.73 73 74 66.73 74 59C74 51.27 67.73 45 60 45Z"
                stroke="url(#searchGrad)"
                strokeWidth="3"
                strokeLinecap="round"
                fill="none"
              />
            </svg>
          </div>
        </div>

        <h3 className={`font-semibold text-gray-800 mb-2 ${currentSize.title}`}>
          {finalTitle}
        </h3>
        {finalDescription && (
          <p
            className={`text-gray-600 mb-6 max-w-md ${currentSize.description}`}
          >
            {finalDescription}
          </p>
        )}

        {showSuggestions && suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 justify-center max-w-md mb-6">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  // Pure UI component - parent handles click
                  if (primaryAction) primaryAction.onClick();
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-full hover:bg-gray-50 hover:border-gray-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {primaryAction && (
          <button
            type="button"
            onClick={primaryAction.onClick}
            className={`inline-flex items-center justify-center font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${currentSize.action}`}
          >
            {primaryAction.label}
          </button>
        )}
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`flex flex-col items-center justify-center text-center ${currentSize.container} ${className}`}
      >
        <div className="mb-4 text-gray-400">
          <svg
            width="80"
            height="80"
            viewBox="0 0 80 80"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="animate-empty-pulse"
            aria-hidden="true"
          >
            <rect
              x="10"
              y="20"
              width="60"
              height="40"
              rx="4"
              stroke="currentColor"
              strokeWidth="2"
              fill="none"
              opacity="0.3"
            />
            <line
              x1="25"
              y1="20"
              x2="25"
              y2="60"
              stroke="currentColor"
              strokeWidth="2"
              opacity="0.2"
            />
            <line
              x1="40"
              y1="20"
              x2="40"
              y2="60"
              stroke="currentColor"
              strokeWidth="2"
              opacity="0.2"
            />
            <line
              x1="55"
              y1="20"
              x2="55"
              y2="60"
              stroke="currentColor"
              strokeWidth="2"
              opacity="0.2"
            />
            <line
              x1="10"
              y1="35"
              x2="70"
              y2="35"
              stroke="currentColor"
              strokeWidth="2"
              opacity="0.2"
            />
            <line
              x1="10"
              y1="50"
              x2="70"
              y2="50"
              stroke="currentColor"
              strokeWidth="2"
              opacity="0.2"
            />
          </svg>
        </div>
        <h3 className={`font-medium text-gray-700 mb-1 ${currentSize.title}`}>
          {finalTitle}
        </h3>
        {finalDescription && (
          <p className={`text-gray-500 mb-4 ${currentSize.description}`}>
            {finalDescription}
          </p>
        )}
        {primaryAction && (
          <button
            type="button"
            onClick={primaryAction.onClick}
            className={`inline-flex items-center justify-center font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${currentSize.action}`}
          >
            {primaryAction.label}
          </button>
        )}
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`flex flex-col items-center justify-center text-center ${currentSize.container} rounded-xl bg-gradient-to-br from-gray-50/80 via-white to-gray-50/60 border border-gray-200/50 shadow-sm ${className}`}
      >
        <div className="mb-4 text-gray-400">
          <DefaultEmptyBoxIllustration />
        </div>
        <h3 className={`font-semibold text-gray-800 mb-2 ${currentSize.title}`}>
          {finalTitle}
        </h3>
        {finalDescription && (
          <p
            className={`text-gray-600 mb-6 max-w-sm ${currentSize.description}`}
          >
            {finalDescription}
          </p>
        )}
        <div className="flex flex-wrap gap-3 justify-center">
          {primaryAction && (
            <button
              type="button"
              onClick={primaryAction.onClick}
              className={`inline-flex items-center justify-center font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${currentSize.action}`}
            >
              {primaryAction.label}
            </button>
          )}
          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className={`inline-flex items-center justify-center font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 ${currentSize.action}`}
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      </div>
    );
  }

  // Default: illustration variant
  return (
    <div
      role="status"
      aria-live="polite"
      className={`bg-white rounded-xl shadow-sm m-4 flex flex-col items-center justify-center text-center relative ${currentSize.container} ${className}`}
    >
      {/* Background gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-br from-blue-100/30 via-purple-100/20 to-pink-100/30 rounded-full blur-3xl animate-empty-orb-1" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-tr from-purple-100/25 via-blue-100/15 to-pink-100/25 rounded-full blur-3xl animate-empty-orb-2" />
      </div>

      {/* Illustration */}
      <div className="relative mb-6 z-10">
        {illustration ? (
          <div className={`${currentSize.illustration} mx-auto`}>
            {illustration}
          </div>
        ) : (
          <div className={`${currentSize.illustration} mx-auto`}>
            <DefaultAIBlobIllustration />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-md">
        <h3 className={`font-semibold text-gray-800 mb-3 ${currentSize.title}`}>
          {finalTitle}
        </h3>
        {finalDescription && (
          <p className={`text-gray-600 mb-8 ${currentSize.description}`}>
            {finalDescription}
          </p>
        )}

        {/* Actions */}
        {(primaryAction || secondaryAction) && (
          <div className="flex flex-wrap gap-3 justify-center">
            {primaryAction && (
              <button
                type="button"
                onClick={primaryAction.onClick}
                className={`inline-flex items-center justify-center font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${currentSize.action}`}
              >
                {primaryAction.label}
              </button>
            )}
            {secondaryAction && (
              <button
                type="button"
                onClick={secondaryAction.onClick}
                className={`inline-flex items-center justify-center font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 ${currentSize.action}`}
              >
                {secondaryAction.label}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(EmptyState);
