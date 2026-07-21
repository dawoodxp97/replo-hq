'use client';

import { motion } from 'framer-motion';
import {
  BarChart3,
  Code,
  Github,
  GraduationCap,
  Network,
  Sparkles,
} from 'lucide-react';

const features = [
  {
    icon: Github,
    title: 'GitHub Repo Analyzer',
    description:
      'Automatically analyze any repository structure using tree-sitter and CodeBERT. Extract function-level mappings and understand code flow instantly.',
    gradient: 'from-indigo-500 to-purple-500',
  },
  {
    icon: Code,
    title: 'Interactive Tutorials',
    description:
      'Edit and run code examples in real-time with our integrated Sandpack editor. Learn by doing with live execution and instant feedback.',
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    icon: GraduationCap,
    title: 'Quizzes & Progress',
    description:
      'AI-generated quizzes based on tutorial content. Track your learning progress with detailed analytics and personalized recommendations.',
    gradient: 'from-pink-500 to-rose-500',
  },
  {
    icon: Network,
    title: 'Diagrams & Visualizations',
    description:
      'Visualize dependency graphs and code relationships using Mermaid.js. Understand complex architectures at a glance.',
    gradient: 'from-cyan-500 to-blue-500',
  },
  {
    icon: Sparkles,
    title: 'Multi-Level Tracks',
    description:
      'Generate beginner, intermediate, and advanced tutorials from the same codebase. Adaptive difficulty based on your progress.',
    gradient: 'from-blue-500 to-indigo-500',
  },
];

const FeaturesGrid = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: [0.42, 0, 0.58, 1] as const,
      },
    },
  };

  return (
    <section id="features" className="py-20 md:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-slate-900 mb-4">
            Everything you need to{' '}
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
              master any codebase
            </span>
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Powerful AI-driven features that transform how developers learn and
            understand code.
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8"
        >
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                variants={itemVariants}
                whileHover={{
                  scale: 1.03,
                  y: -5,
                  transition: { duration: 0.2 },
                }}
                className="group relative bg-white rounded-2xl p-6 lg:p-8 border border-slate-200 hover:border-transparent hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2"
              >
                {/* Gradient background on hover */}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-300`}
                ></div>

                {/* Icon */}
                <div className="relative mb-4">
                  <div
                    className={`w-12 h-12 lg:w-14 lg:h-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-110`}
                  >
                    <Icon className="w-6 h-6 lg:w-7 lg:h-7 text-white" />
                  </div>
                </div>

                {/* Content */}
                <h3 className="text-xl lg:text-2xl font-bold text-slate-900 mb-3 group-hover:text-indigo-600 transition-colors duration-200">
                  {feature.title}
                </h3>
                <p className="text-slate-600 leading-relaxed">
                  {feature.description}
                </p>

                {/* Decorative accent */}
                <div
                  className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${feature.gradient} rounded-b-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
                ></div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-16 text-center"
        >
          <p className="text-slate-600 mb-6">
            Ready to transform your learning experience?
          </p>
          <a
            href="/login"
            className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 text-white font-semibold rounded-lg shadow-xl shadow-indigo-500/25 hover:shadow-2xl hover:shadow-indigo-500/30 transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Get Started Free
          </a>
        </motion.div>
      </div>
    </section>
  );
};

export default FeaturesGrid;
