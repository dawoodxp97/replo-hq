import { memo } from 'react';

export type ErrorVariant = 'full' | 'inline' | 'toast' | 'card' | 'minimal';

export interface ErrorProps {
  variant?: ErrorVariant;
  title?: string;
  message?: string;
  error?: Error | string | unknown;
  className?: string;
  icon?: React.ReactNode;
}

const isErrorLike = (value: unknown): value is Error => {
  return (
    typeof value === 'object' &&
    value !== null &&
    'message' in value &&
    typeof (value as Error).message === 'string'
  );
};

const extractErrorMessage = (error: Error | string | unknown): string => {
  if (!error) return 'An unexpected error occurred';
  if (typeof error === 'string') return error;
  if (isErrorLike(error)) {
    return error.message || error.name || 'An error occurred';
  }
  if (typeof error === 'object' && error !== null) {
    const obj = error as Record<string, unknown>;
    if (obj.message && typeof obj.message === 'string') return obj.message;
    if (obj.error && typeof obj.error === 'string') return obj.error;
  }
  return 'An unexpected error occurred';
};

const AnimatedErrorIcon = ({
  className = 'w-12 h-12',
  animationType = 'float',
}: {
  className?: string;
  animationType?: 'float' | 'pulse' | 'rotate' | 'wave';
}) => {
  const iconId = `error-icon-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <svg
      className={className}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient
          id={`errorGradient-${iconId}`}
          x1="0%"
          y1="0%"
          x2="100%"
          y2="100%"
        >
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
          <stop offset="50%" stopColor="#f87171" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#fca5a5" stopOpacity="0.4" />
        </linearGradient>
        <radialGradient id={`errorGlow-${iconId}`}>
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
        </radialGradient>
        <filter id={`glow-${iconId}`}>
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Outer glow ring - rotating */}
      <circle
        cx="60"
        cy="60"
        r="55"
        fill="none"
        stroke="url(#errorGradient)"
        strokeWidth="2"
        strokeOpacity="0.3"
        className={
          animationType === 'rotate'
            ? 'animate-spin-slow'
            : animationType === 'wave'
            ? 'animate-error-wave'
            : 'animate-pulse-glow'
        }
      />

      {/* Main circle with gradient */}
      <circle
        cx="60"
        cy="60"
        r="50"
        fill={`url(#errorGradient-${iconId})`}
        className={
          animationType === 'pulse'
            ? 'animate-pulse-soft'
            : animationType === 'float'
            ? 'animate-error-float'
            : 'animate-pulse-glow'
        }
      />

      {/* Inner glow */}
      <circle
        cx="60"
        cy="60"
        r="45"
        fill={`url(#errorGlow-${iconId})`}
        className={
          animationType === 'float'
            ? 'animate-error-float-delayed'
            : 'animate-pulse-glow'
        }
      />

      {/* Error symbol - X */}
      <g
        className={
          animationType === 'wave'
            ? 'animate-error-symbol-wave'
            : animationType === 'float'
            ? 'animate-error-symbol-float'
            : ''
        }
      >
        <path
          d="M45 45 L75 75 M75 45 L45 75"
          stroke="currentColor"
          strokeWidth="6"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-red-500"
          filter={`url(#glow-${iconId})`}
        />
      </g>

      {/* Floating particles */}
      {animationType === 'float' && (
        <>
          <circle
            cx="30"
            cy="30"
            r="3"
            fill="#ef4444"
            opacity="0.6"
            className="animate-error-particle-1"
          />
          <circle
            cx="90"
            cy="40"
            r="2.5"
            fill="#f87171"
            opacity="0.5"
            className="animate-error-particle-2"
          />
          <circle
            cx="85"
            cy="85"
            r="2"
            fill="#fca5a5"
            opacity="0.4"
            className="animate-error-particle-3"
          />
        </>
      )}
    </svg>
  );
};

const MinimalErrorIcon = ({
  className = 'w-4 h-4',
}: {
  className?: string;
}) => (
  <svg
    className={`${className} animate-error-minimal-pulse`}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    aria-hidden="true"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

// Floating error badges for background decoration
const FloatingErrorBadge = ({
  x = 0,
  y = 0,
  delay = 0,
}: {
  x?: number;
  y?: number;
  delay?: number;
}) => (
  <div
    className="absolute animate-error-badge-float pointer-events-none opacity-30"
    style={{
      left: `${x}%`,
      top: `${y}%`,
      animationDelay: `${delay}s`,
    }}
  >
    <svg
      className="w-8 h-8 text-red-400"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  </div>
);

// Small warning icon elements
const WarningDot = ({ delay = 0 }: { delay?: number }) => (
  <div
    className="absolute w-2 h-2 bg-red-400 rounded-full animate-error-dot-float opacity-40"
    style={{ animationDelay: `${delay}s` }}
  />
);

// ============================================================================
// Main Error Component
// ============================================================================

const Error = (props: ErrorProps) => {
  const {
    variant = 'full',
    title,
    message,
    error,
    className = '',
    icon,
  } = props;

  const errorMessage =
    message || extractErrorMessage(error || 'An unexpected error occurred');
  const errorTitle = title || 'Error';

  // Base classes for all variants
  const baseClasses = 'transition-all duration-300 ease-out';

  // Variant-specific rendering
  switch (variant) {
    case 'full':
      return (
        <div
          role="alert"
          aria-live="assertive"
          className={`${baseClasses} !mt-0 ml-2 mr-2 shadow-[0px_7px_29px_0px_rgba(100,100,111,0.2)] rounded-2xl flex items-center justify-center p-4 relative overflow-hidden ${className}`}
          style={{
            background:
              'linear-gradient(135deg, rgba(254, 242, 242, 0.4) 0%, rgba(255, 255, 255, 0.8) 25%, rgba(255, 245, 245, 0.6) 50%, rgba(255, 255, 255, 0.9) 75%, rgba(254, 242, 242, 0.3) 100%)',
          }}
        >
          {/* Modern AI gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-rose-50/60 via-white/90 to-pink-50/50" />

          {/* Floating background orbs with modern colors */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-rose-200/20 via-pink-100/15 to-rose-100/10 rounded-full blur-3xl animate-error-orb-1" />
            <div className="absolute bottom-10 right-10 w-[32rem] h-[32rem] bg-gradient-to-tr from-pink-200/15 via-rose-100/20 to-pink-50/10 rounded-full blur-3xl animate-error-orb-2" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40rem] h-[40rem] bg-gradient-to-br from-rose-100/10 via-pink-50/5 to-transparent rounded-full blur-3xl animate-error-orb-3" />
          </div>

          {/* Floating error icons */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <FloatingErrorBadge x={10} y={15} delay={0} />
            <FloatingErrorBadge x={85} y={20} delay={1.5} />
            <FloatingErrorBadge x={15} y={80} delay={3} />
            <FloatingErrorBadge x={90} y={75} delay={4.5} />
            <FloatingErrorBadge x={50} y={10} delay={2} />
            <FloatingErrorBadge x={5} y={50} delay={5} />
          </div>

          {/* Warning dots */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-[15%] left-[20%]">
              <WarningDot delay={0.5} />
            </div>
            <div className="absolute top-[25%] right-[25%]">
              <WarningDot delay={2} />
            </div>
            <div className="absolute bottom-[20%] left-[30%]">
              <WarningDot delay={3.5} />
            </div>
            <div className="absolute bottom-[30%] right-[15%]">
              <WarningDot delay={1} />
            </div>
          </div>

          <div className="max-w-lg w-full text-center animate-fade-in-slide relative z-10">
            <div className="relative mb-6 flex justify-center">
              {icon || (
                <AnimatedErrorIcon
                  className="w-24 h-24 text-red-500"
                  animationType="float"
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-r from-red-400/20 via-rose-300/15 to-pink-200/20 blur-3xl rounded-full animate-pulse-glow" />
            </div>

            <h1 className="text-3xl font-bold mb-3 bg-gradient-to-r from-red-600 via-rose-500 to-pink-500 bg-clip-text text-transparent animate-fade-in-slide">
              {errorTitle}
            </h1>
            <p className="text-lg text-gray-700 mb-6 leading-relaxed animate-fade-in-slide">
              {errorMessage}
            </p>
          </div>
        </div>
      );

    case 'inline':
      return (
        <div
          role="alert"
          aria-live="polite"
          className={`relative overflow-hidden border-l-4 border-red-400 rounded-2xl p-4 shadow-sm ${baseClasses} animate-slide-in-right ${className}`}
          style={{
            background:
              'linear-gradient(135deg, rgba(254, 242, 242, 0.6) 0%, rgba(255, 255, 255, 0.9) 50%, rgba(255, 245, 245, 0.7) 100%)',
          }}
        >
          {/* Subtle gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-rose-50/40 via-white/60 to-pink-50/30" />

          {/* Small floating icon */}
          <div className="absolute top-2 right-2 opacity-20">
            <AnimatedErrorIcon
              className="w-4 h-4 text-red-400"
              animationType="float"
            />
          </div>

          <div className="flex items-start gap-3 relative z-10">
            <div className="flex-shrink-0 mt-0.5">
              {icon || (
                <AnimatedErrorIcon
                  className="w-5 h-5 text-red-500"
                  animationType="pulse"
                />
              )}
            </div>
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-sm font-semibold text-red-800 mb-1">
                  {title}
                </h3>
              )}
              <p className="text-sm text-gray-700">{errorMessage}</p>
            </div>
          </div>
        </div>
      );

    case 'toast':
      return (
        <div
          role="alert"
          aria-live="assertive"
          className={`fixed bottom-6 right-6 z-50 max-w-md w-full rounded-xl shadow-2xl border border-red-200/50 p-4 backdrop-blur-sm ${baseClasses} animate-slide-up ${className}`}
          style={{
            background:
              'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(254, 242, 242, 0.92) 50%, rgba(255, 245, 245, 0.98) 100%)',
          }}
        >
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-rose-50/30 via-white/80 to-pink-50/40 rounded-xl" />

          {/* Small floating elements */}
          <div className="absolute top-1 right-1 w-2 h-2 bg-red-400/30 rounded-full animate-error-dot-float opacity-60" />
          <div
            className="absolute bottom-2 left-2 w-1.5 h-1.5 bg-pink-400/40 rounded-full animate-error-dot-float opacity-50"
            style={{ animationDelay: '1s' }}
          />

          <div className="flex items-start gap-3 relative z-10">
            <div className="flex-shrink-0 mt-0.5">
              {icon || (
                <div className="relative">
                  <div className="w-6 h-6 bg-gradient-to-br from-red-500 via-rose-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-lg animate-error-toast-icon">
                    !
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-br from-red-400/40 via-rose-400/30 to-pink-400/40 blur-md rounded-full animate-pulse-glow" />
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-sm font-semibold text-gray-900 mb-1">
                  {title}
                </h3>
              )}
              <p className="text-sm text-gray-700">{errorMessage}</p>
            </div>
          </div>
        </div>
      );

    case 'card':
      return (
        <div
          role="alert"
          aria-live="polite"
          className={`relative overflow-hidden rounded-2xl p-6 shadow-lg border border-red-200/40 ${baseClasses} animate-fade-in-scale ${className}`}
          style={{
            background:
              'linear-gradient(135deg, rgba(254, 242, 242, 0.5) 0%, rgba(255, 255, 255, 0.9) 30%, rgba(255, 245, 245, 0.7) 70%, rgba(254, 242, 242, 0.4) 100%)',
          }}
        >
          {/* Modern gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-rose-50/50 via-white/70 to-pink-50/40 rounded-2xl" />

          {/* Decorative floating icons */}
          <div className="absolute top-4 right-4 opacity-20">
            <FloatingErrorBadge x={0} y={0} delay={0} />
          </div>
          <div className="absolute bottom-4 left-4 opacity-15">
            <FloatingErrorBadge x={0} y={0} delay={2} />
          </div>

          {/* Warning dots */}
          <div className="absolute top-6 left-6">
            <WarningDot delay={0.5} />
          </div>
          <div className="absolute bottom-6 right-6">
            <WarningDot delay={2.5} />
          </div>

          <div className="text-center mb-4 relative z-10">
            <div className="relative inline-block mb-4">
              {icon || (
                <AnimatedErrorIcon
                  className="w-16 h-16 text-red-500 mx-auto"
                  animationType="wave"
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-r from-red-400/25 via-rose-300/20 to-pink-200/25 blur-2xl rounded-full animate-pulse-glow" />
            </div>
            <h2 className="text-xl font-bold mb-2 bg-gradient-to-r from-red-600 via-rose-500 to-pink-500 bg-clip-text text-transparent">
              {errorTitle}
            </h2>
            <p className="text-gray-700 leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      );

    case 'minimal':
      return (
        <div
          role="alert"
          aria-live="polite"
          className={`flex items-center gap-2 text-red-600 ${baseClasses} ${className}`}
        >
          {icon || <MinimalErrorIcon className="w-4 h-4 flex-shrink-0" />}
          <span className="text-sm font-medium truncate">{errorMessage}</span>
        </div>
      );

    default:
      return null;
  }
};

export default memo(Error);
