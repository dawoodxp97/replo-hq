'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';

// Define the repository type
interface Repository {
  repo_id: string;
  github_url: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface RepoListResponse {
  repositories: Repository[];
}

const RepoList = () => {
  // Fetch repositories with polling for status changes
  const { data, isLoading, error } = useQuery<RepoListResponse>({
    queryKey: ['repos'],
    queryFn: async () => {
      const response = await apiClient.get(API_ENDPOINTS.REPO_GET_ALL);
      return response as unknown as RepoListResponse;
    },
    // Poll every 5 seconds if any repo is in PENDING or ANALYZING state
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
  });

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Your Repositories</h2>
        <div className="flex justify-center items-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Your Repositories</h2>
        <div className="p-4 text-red-600">
          Failed to load repositories. Please try again later.
        </div>
      </div>
    );
  }

  const repositories = data?.repositories || [];

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Your Repositories</h2>
      
      {repositories.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No repositories found. Submit a GitHub repository to get started.
        </div>
      ) : (
        <div className="space-y-4">
          {repositories.map((repo) => (
            <div key={repo.repo_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium text-lg">{repo.name}</h3>
                  <p className="text-sm text-gray-600 truncate">{repo.github_url}</p>
                </div>
                <StatusBadge status={repo.status} />
              </div>
              
              {repo.description && (
                <p className="mt-2 text-sm text-gray-700">{repo.description}</p>
              )}
              
              <div className="mt-4 flex justify-between items-center">
                <div className="text-xs text-gray-500">
                  Added: {new Date(repo.created_at).toLocaleDateString()}
                </div>
                
                {repo.status === 'COMPLETED' && (
                  <Link 
                    href={`/repo/${repo.repo_id}`}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    View Tutorials
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Status badge component
const StatusBadge = ({ status }: { status: string }) => {
  let bgColor = 'bg-gray-200';
  let textColor = 'text-gray-800';
  
  switch (status) {
    case 'PENDING':
      bgColor = 'bg-yellow-100';
      textColor = 'text-yellow-800';
      break;
    case 'ANALYZING':
      bgColor = 'bg-blue-100';
      textColor = 'text-blue-800';
      break;
    case 'COMPLETED':
      bgColor = 'bg-green-100';
      textColor = 'text-green-800';
      break;
    case 'FAILED':
      bgColor = 'bg-red-100';
      textColor = 'text-red-800';
      break;
  }
  
  return (
    <span className={`${bgColor} ${textColor} text-xs px-2 py-1 rounded-full font-medium`}>
      {status}
    </span>
  );
};

export default RepoList;