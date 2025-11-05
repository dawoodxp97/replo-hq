'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Quote, Star } from 'lucide-react';

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'Senior Frontend Developer',
    company: 'TechCorp',
    image: '👩‍💻',
    content:
      'Replo AI transformed how our team onboards new developers. Instead of spending days reading documentation, new team members can now understand our codebase through interactive tutorials in hours.',
    rating: 5,
  },
  {
    name: 'Michael Rodriguez',
    role: 'Engineering Lead',
    company: 'StartupXYZ',
    image: '👨‍💼',
    content:
      'The AI-generated quizzes and progress tracking are game-changers. Our junior developers are learning faster and retaining more. The interactive code editor makes experimentation risk-free.',
    rating: 5,
  },
  {
    name: 'Emily Johnson',
    role: 'Full-Stack Developer',
    company: 'DevStudio',
    image: '👩‍🔬',
    content:
      'I love how Replo AI adapts tutorials to different skill levels. The dependency graphs help me visualize complex architectures, and the real-time code execution means I can learn by doing.',
    rating: 5,
  },
];

const Testimonials = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
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
        ease: 'easeOut',
      },
    },
  };

  return (
    <section id="testimonials" className="py-20 md:py-32 bg-white">
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
            Loved by{' '}
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
              developers worldwide
            </span>
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            See what developers are saying about Replo AI
          </p>
        </motion.div>

        {/* Testimonials Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8"
        >
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.name}
              variants={itemVariants}
              whileHover={{
                scale: 1.02,
                y: -5,
                transition: { duration: 0.2 },
              }}
              className="bg-gradient-to-br from-white to-slate-50 rounded-2xl p-6 lg:p-8 border border-slate-200 hover:border-indigo-200 hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 flex flex-col"
            >
              {/* Quote Icon */}
              <div className="mb-4">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                  <Quote className="w-5 h-5 text-white" />
                </div>
              </div>

              {/* Rating */}
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="w-4 h-4 fill-yellow-400 text-yellow-400"
                  />
                ))}
              </div>

              {/* Content */}
              <p className="text-slate-700 mb-6 flex-1 leading-relaxed">
                "{testimonial.content}"
              </p>

              {/* Author */}
              <div className="flex items-center gap-4 pt-4 border-t border-slate-200">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-400 flex items-center justify-center text-2xl flex-shrink-0">
                  {testimonial.image}
                </div>
                <div>
                  <div className="font-semibold text-slate-900">
                    {testimonial.name}
                  </div>
                  <div className="text-sm text-slate-500">
                    {testimonial.role} at {testimonial.company}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default Testimonials;
