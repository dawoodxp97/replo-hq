'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';

// Define types
interface Repository {
  repo_id: string;
  github_url: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Tutorial {
  tutorial_id: string;
  level: string;
  title: string;
}

interface RepoDetailResponse {
  repository: Repository;
  tutorials: Tutorial[];
}

export default function RepoDetailPage() {
  const params = useParams();
  const repoId = params.repoId as string;

  // Fetch repository details
  const { data, isLoading, error } = useQuery<RepoDetailResponse>({
    queryKey: ['repo', repoId],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.REPO_GET_BY_ID(repoId));
    },
    // Only fetch if we have a repoId
    enabled: !!repoId,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 p-4 rounded-lg text-red-700 mb-4">
          Failed to load repository details. Please try again later.
        </div>
        <Link href="/dashboard" className="text-blue-600 hover:underline">
          &larr; Back to Dashboard
        </Link>
      </div>
    );
  }

  const { repository, tutorials } = data;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/dashboard" className="text-blue-600 hover:underline">
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h1 className="text-3xl font-bold mb-2">{repository.name}</h1>
        <p className="text-gray-600 mb-4">
          <a 
            href={repository.github_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="hover:underline"
          >
            {repository.github_url}
          </a>
        </p>
        
        {repository.description && (
          <p className="mb-4">{repository.description}</p>
        )}
        
        <div className="flex items-center text-sm text-gray-500">
          <span className="mr-4">Status: {repository.status}</span>
          <span>Last updated: {new Date(repository.updated_at).toLocaleString()}</span>
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-4">Available Tutorials</h2>
      
      {tutorials.length === 0 ? (
        <div className="bg-yellow-50 p-4 rounded-lg text-yellow-700">
          No tutorials available yet. If the repository status is "ANALYZING", please check back later.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tutorials.map((tutorial) => (
            <Link 
              key={tutorial.tutorial_id} 
              href={`/tutorial/${tutorial.tutorial_id}`}
              className="block"
            >
              <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow border-l-4 border-blue-600">
                <h3 className="text-xl font-semibold mb-2">{tutorial.title}</h3>
                <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full inline-block">
                  {tutorial.level}
                </div>
                <p className="mt-4 text-gray-600">
                  Click to start learning with this tutorial
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}