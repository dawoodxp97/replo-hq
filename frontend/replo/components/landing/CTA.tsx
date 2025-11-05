'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, CheckCircle, Loader2 } from 'lucide-react';

const CTA = () => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setErrorMessage('');

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      setStatus('success');
      setEmail('');
      
      // Reset success message after 5 seconds
      setTimeout(() => {
        setStatus('idle');
      }, 5000);
    } catch (error) {
      setStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to subscribe. Please try again.');
    }
  };

  return (
    <section className="py-20 md:py-32 bg-gradient-to-br from-indigo-600 via-purple-600 to-cyan-600 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4">
            Ready to transform your codebase into tutorials?
          </h2>
          <p className="text-lg md:text-xl text-indigo-100 mb-10 max-w-2xl mx-auto">
            Join thousands of developers using Replo AI to create interactive learning experiences. Get started in minutes.
          </p>

          {/* Email Subscription Form */}
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            onSubmit={handleSubmit}
            className="max-w-md mx-auto"
          >
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                  disabled={status === 'loading' || status === 'success'}
                  className="w-full pl-12 pr-4 py-4 rounded-lg bg-white text-slate-900 placeholder-slate-400 border-0 focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Email address"
                />
              </div>
              <button
                type="submit"
                disabled={status === 'loading' || status === 'success'}
                className="px-8 py-4 bg-white text-indigo-600 font-semibold rounded-lg shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2 whitespace-nowrap"
              >
                {status === 'loading' ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Subscribing...
                  </>
                ) : status === 'success' ? (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Subscribed!
                  </>
                ) : (
                  <>
                    Get Started
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>

            {/* Error Message */}
            {status === 'error' && errorMessage && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 text-red-200 text-sm text-center"
                role="alert"
              >
                {errorMessage}
              </motion.p>
            )}

            {/* Success Message */}
            {status === 'success' && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 text-white text-sm text-center"
              >
                Thanks for subscribing! We'll be in touch soon.
              </motion.p>
            )}

            {/* Privacy Note */}
            <p className="mt-6 text-sm text-indigo-100">
              We respect your privacy. Unsubscribe at any time.
            </p>
          </motion.form>

          {/* Alternative CTA */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-12"
          >
            <a
              href="/login"
              className="inline-flex items-center text-white font-semibold hover:text-indigo-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-indigo-600 rounded px-4 py-2"
            >
              Or sign in to your account
              <ArrowRight className="ml-2 w-5 h-5" />
            </a>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default CTA;
