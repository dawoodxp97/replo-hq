'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sandpack } from '@codesandbox/sandpack-react';
import { Play, Code2, Sparkles } from 'lucide-react';

const DemoSplit = () => {
  const [activeTab, setActiveTab] = useState<'explanation' | 'code'>(
    'explanation'
  );

  // Simple React example for Sandpack
  const sandpackFiles = {
    '/App.js': `import { useState } from 'react';

export default function App() {
  const [count, setCount] = useState(0);

  return (
    <div style={{ 
      padding: '2rem', 
      fontFamily: 'system-ui',
      textAlign: 'center'
    }}>
      <h1 style={{ 
        background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        fontSize: '2.5rem',
        marginBottom: '1rem'
      }}>
        Welcome to Replo AI
      </h1>
      <p style={{ color: '#64748b', marginBottom: '2rem' }}>
        Try editing this code and see the results update in real-time!
      </p>
      <button
        onClick={() => setCount(count + 1)}
        style={{
          padding: '0.75rem 1.5rem',
          fontSize: '1rem',
          fontWeight: '600',
          color: 'white',
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          border: 'none',
          borderRadius: '0.5rem',
          cursor: 'pointer',
          boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)'
        }}
      >
        Count: {count}
      </button>
    </div>
  );
}`,
    '/package.json': `{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}`,
  };

  return (
    <section
      id="demo"
      className="py-20 md:py-32 bg-gradient-to-br from-slate-50 to-indigo-50/30"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/60 backdrop-blur-sm rounded-full border border-indigo-100 mb-4 shadow-sm">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span className="text-sm font-medium text-slate-700">
              Interactive Demo
            </span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-slate-900 mb-4">
            See it in{' '}
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
              action
            </span>
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Experience how Replo AI transforms code into interactive learning
            experiences. Edit the code below and watch it update live.
          </p>
        </motion.div>

        {/* Split View Container */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="grid lg:grid-cols-2 gap-6 lg:gap-8"
        >
          {/* Left: Explanation */}
          <div className="order-2 lg:order-1">
            <div className="bg-white rounded-2xl p-6 lg:p-8 shadow-xl border border-slate-200 h-full flex flex-col">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                  <Code2 className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900">
                  How it works
                </h3>
              </div>

              <div className="space-y-4 flex-1">
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
                    1
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Analyze your repository
                    </h4>
                    <p className="text-slate-600 text-sm">
                      Connect any GitHub repo. Our AI analyzes the code
                      structure, dependencies, and architecture patterns.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 font-bold text-sm">
                    2
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Generate interactive tutorials
                    </h4>
                    <p className="text-slate-600 text-sm">
                      AI creates step-by-step lessons with code examples,
                      explanations, and visual diagrams tailored to your skill
                      level.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-100 flex items-center justify-center text-cyan-600 font-bold text-sm">
                    3
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">
                      Learn by doing
                    </h4>
                    <p className="text-slate-600 text-sm">
                      Edit code directly in the browser, see results instantly,
                      and track your progress as you master each concept.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-slate-200">
                <a
                  href="/login"
                  className="inline-flex items-center justify-center w-full px-6 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 text-white font-semibold rounded-lg shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Start Learning Now
                  <Play className="ml-2 w-5 h-5" />
                </a>
              </div>
            </div>
          </div>

          {/* Right: Interactive Code Editor */}
          <div className="order-1 lg:order-2">
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden h-full">
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                  <div className="w-3 h-3 rounded-full bg-green-400"></div>
                </div>
                <span className="ml-2 text-xs text-slate-500 font-mono">
                  interactive-demo.jsx
                </span>
              </div>
              <div className="h-[500px] lg:h-[600px]">
                <Sandpack
                  template="react"
                  files={sandpackFiles}
                  theme="light"
                  options={{
                    showNavigator: false,
                    showTabs: true,
                    showLineNumbers: true,
                    showInlineErrors: true,
                    wrapContent: true,
                    editorHeight: '100%',
                    editorWidthPercentage: 50,
                  }}
                  customSetup={{
                    dependencies: {
                      react: '^18.2.0',
                      'react-dom': '^18.2.0',
                    },
                  }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default DemoSplit;
