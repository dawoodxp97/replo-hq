'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';

const RepoSubmitForm = () => {
  const [githubUrl, setGithubUrl] = useState('');
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  // Mutation for submitting a repository
  const { mutate, isPending } = useMutation({
    mutationFn: async (url: string) => {
      return apiClient.post(API_ENDPOINTS.REPO_ANALYZE, { github_url: url });
    },
    onSuccess: () => {
      // Reset form and invalidate repos query to refresh the list
      setGithubUrl('');
      setError('');
      queryClient.invalidateQueries({ queryKey: ['repos'] });
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to submit repository');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!githubUrl.trim()) {
      setError('Please enter a GitHub URL');
      return;
    }

    // Simple GitHub URL validation
    if (!githubUrl.includes('github.com/')) {
      setError('Please enter a valid GitHub repository URL');
      return;
    }

    // Submit the form
    mutate(githubUrl);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Submit a GitHub Repository</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="githubUrl" className="block text-sm font-medium text-gray-700 mb-1">
            GitHub Repository URL
          </label>
          <input
            id="githubUrl"
            type="text"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="https://github.com/username/repository"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isPending}
          />
          {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        </div>
        <button
          type="submit"
          disabled={isPending}
          className={`w-full px-4 py-2 text-white font-medium rounded-md ${
            isPending ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
          } focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`}
        >
          {isPending ? 'Submitting...' : 'Generate Tutorials'}
        </button>
      </form>
    </div>
  );
};

export default RepoSubmitForm;