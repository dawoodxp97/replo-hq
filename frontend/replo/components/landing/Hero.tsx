'use client';

import React from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';

const HeroFallbackSVG = () => (
  <div className="w-full h-full flex items-center justify-center">
    <svg
      viewBox="0 0 400 400"
      className="w-full h-full max-w-md"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="50%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>
      <circle
        cx="200"
        cy="200"
        r="80"
        fill="url(#grad1)"
        opacity="0.3"
        className="animate-pulse"
      >
        <animate
          attributeName="r"
          values="80;100;80"
          dur="3s"
          repeatCount="indefinite"
        />
      </circle>
      <circle cx="200" cy="200" r="60" fill="url(#grad1)" opacity="0.5">
        <animate
          attributeName="r"
          values="60;70;60"
          dur="2s"
          repeatCount="indefinite"
        />
      </circle>
      <circle cx="200" cy="200" r="40" fill="url(#grad1)" opacity="0.7" />
      <path
        d="M180 180 L220 200 L180 220 Z"
        fill="white"
        opacity="0.9"
        className="animate-pulse"
      />
    </svg>
  </div>
);

const Hero = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.42, 0, 0.58, 1] as const,
      },
    },
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20 md:pt-24 bg-gradient-to-br from-indigo-50 via-purple-50 to-cyan-50">
      {/* Animated background gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-indigo-400/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl animate-float-delay-1"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-cyan-400/20 rounded-full blur-3xl animate-float-delay-2"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text Content */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="text-center lg:text-left"
          >
            <motion.div
              variants={itemVariants}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white/60 backdrop-blur-sm rounded-full border border-indigo-100 mb-6 shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-slate-700">
                AI-Powered Code Learning
              </span>
            </motion.div>

            <motion.h1
              variants={itemVariants}
              className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 mb-6 leading-tight"
            >
              Turn any codebase into{' '}
              <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
                step-by-step interactive tutorials
              </span>{' '}
              automatically
            </motion.h1>

            <motion.p
              variants={itemVariants}
              className="text-lg md:text-xl text-slate-600 mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed"
            >
              Analyze any GitHub repository and instantly generate comprehensive
              tutorials with interactive examples, diagrams, and quizzes.
              Perfect for developers at any level.
            </motion.p>

            <motion.div
              variants={itemVariants}
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
            >
              <Link
                href="/login"
                className="group inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 text-white font-semibold rounded-lg shadow-xl shadow-indigo-500/25 hover:shadow-2xl hover:shadow-indigo-500/30 transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Try a Demo
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="#demo"
                className="inline-flex items-center justify-center px-8 py-4 bg-white text-slate-700 font-semibold rounded-lg border-2 border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                See Docs
              </Link>
            </motion.div>

            {/* Trust indicators */}
            <motion.div
              variants={itemVariants}
              className="mt-12 flex flex-wrap items-center justify-center lg:justify-start gap-6 text-sm text-slate-500"
            >
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Free to start</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span>5-minute setup</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Right: Animated Graphic */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="relative"
          >
            {/* Glassmorphism card container */}
            <div className="relative bg-white/40 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-white/50 min-h-[400px] flex items-center justify-center">
              {/* Using fallback SVG for now - replace with Lottie when you have a file */}
              <HeroFallbackSVG />
              {/* TODO: Uncomment and add your Lottie file path when ready
              {typeof window !== 'undefined' && (
                <LottiePlayer
                  src="/animations/hero-animation.json"
                  loop
                  autoplay
                  className="w-full h-full"
                  fallback={<HeroFallbackSVG />}
                />
              )}
              */}
            </div>

            {/* Floating code snippets (decorative) */}
            <motion.div
              animate={{
                y: [0, -10, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="absolute -top-4 -left-4 bg-white/80 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-slate-200 hidden md:block"
            >
              <div className="text-xs font-mono text-slate-700">
                <div className="text-indigo-600">function</div>
                <div className="text-purple-600">generateTutorial</div>
              </div>
            </motion.div>
            <motion.div
              animate={{
                y: [0, 10, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: 1,
              }}
              className="absolute -bottom-4 -right-4 bg-white/80 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-slate-200 hidden md:block"
            >
              <div className="text-xs font-mono text-slate-700">
                <div className="text-cyan-600">const</div>
                <div className="text-purple-600">tutorial</div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
      >
        <motion.div
          animate={{
            y: [0, 8, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="w-6 h-10 border-2 border-slate-400 rounded-full flex justify-center p-2"
        >
          <div className="w-1 h-3 bg-slate-400 rounded-full"></div>
        </motion.div>
      </motion.div>
    </section>
  );
};

export default Hero;
