'use client';

import { memo } from 'react';
import Loader from './Loader';

interface InitialLoaderProps {
  message?: string;
}

const InitialLoader = ({ message = 'Initializing...' }: InitialLoaderProps) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-slate-50 via-purple-50/30 to-blue-50/30 backdrop-blur-sm">
      {/* AI Aesthetic Background Particles */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Floating gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-r from-purple-400/20 via-pink-400/20 to-blue-400/20 rounded-full blur-3xl animate-ai-orb-1"></div>
        <div className="absolute top-3/4 right-1/4 w-80 h-80 bg-gradient-to-r from-blue-400/20 via-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-ai-orb-2"></div>
        <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-gradient-to-r from-pink-400/20 via-blue-400/20 to-purple-400/20 rounded-full blur-3xl animate-ai-orb-3"></div>

        {/* Animated grid pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#8b5cf6_1px,transparent_1px),linear-gradient(to_bottom,#8b5cf6_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] animate-ai-grid"></div>
        </div>

        {/* Floating particles */}
        <div className="absolute top-1/3 left-1/3 w-2 h-2 bg-purple-400 rounded-full blur-sm animate-ai-particle-1"></div>
        <div className="absolute top-2/3 right-1/3 w-1.5 h-1.5 bg-pink-400 rounded-full blur-sm animate-ai-particle-2"></div>
        <div className="absolute bottom-1/3 left-2/3 w-2.5 h-2.5 bg-blue-400 rounded-full blur-sm animate-ai-particle-3"></div>
        <div className="absolute top-1/2 right-1/4 w-1.5 h-1.5 bg-purple-300 rounded-full blur-sm animate-ai-particle-4"></div>
      </div>

      {/* Main loader content */}
      <div className="relative z-10 flex flex-col items-center justify-center gap-6">
        {/* AI Loader */}
        <Loader type="ai" size="lg" message={message} />

        {/* Subtle glow effect around loader */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-blue-500/10 rounded-full blur-3xl animate-ai-glow"></div>
        </div>
      </div>

      <style jsx>{`
        @keyframes ai-orb-1 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.3;
          }
          33% {
            transform: translate(30px, -40px) scale(1.1);
            opacity: 0.4;
          }
          66% {
            transform: translate(-20px, 30px) scale(0.9);
            opacity: 0.35;
          }
        }

        @keyframes ai-orb-2 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.25;
          }
          33% {
            transform: translate(-40px, 30px) scale(1.15);
            opacity: 0.35;
          }
          66% {
            transform: translate(25px, -35px) scale(0.95);
            opacity: 0.3;
          }
        }

        @keyframes ai-orb-3 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.2;
          }
          33% {
            transform: translate(35px, 25px) scale(1.05);
            opacity: 0.3;
          }
          66% {
            transform: translate(-30px, -20px) scale(0.98);
            opacity: 0.25;
          }
        }

        @keyframes ai-grid {
          0% {
            transform: translate(0, 0);
          }
          100% {
            transform: translate(4rem, 4rem);
          }
        }

        @keyframes ai-particle-1 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.6;
          }
          50% {
            transform: translate(20px, -30px) scale(1.2);
            opacity: 0.8;
          }
        }

        @keyframes ai-particle-2 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.5;
          }
          50% {
            transform: translate(-25px, 25px) scale(1.15);
            opacity: 0.7;
          }
        }

        @keyframes ai-particle-3 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.55;
          }
          50% {
            transform: translate(30px, 20px) scale(1.1);
            opacity: 0.75;
          }
        }

        @keyframes ai-particle-4 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.5;
          }
          50% {
            transform: translate(-20px, -25px) scale(1.25);
            opacity: 0.7;
          }
        }

        @keyframes ai-glow {
          0%,
          100% {
            opacity: 0.4;
            transform: translate(-50%, -50%) scale(1);
          }
          50% {
            opacity: 0.6;
            transform: translate(-50%, -50%) scale(1.1);
          }
        }

        .animate-ai-orb-1 {
          animation: ai-orb-1 8s ease-in-out infinite;
        }

        .animate-ai-orb-2 {
          animation: ai-orb-2 10s ease-in-out infinite;
        }

        .animate-ai-orb-3 {
          animation: ai-orb-3 12s ease-in-out infinite;
        }

        .animate-ai-grid {
          animation: ai-grid 20s linear infinite;
        }

        .animate-ai-particle-1 {
          animation: ai-particle-1 4s ease-in-out infinite;
        }

        .animate-ai-particle-2 {
          animation: ai-particle-2 5s ease-in-out infinite 0.5s;
        }

        .animate-ai-particle-3 {
          animation: ai-particle-3 6s ease-in-out infinite 1s;
        }

        .animate-ai-particle-4 {
          animation: ai-particle-4 4.5s ease-in-out infinite 1.5s;
        }

        .animate-ai-glow {
          animation: ai-glow 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default memo(InitialLoader);
