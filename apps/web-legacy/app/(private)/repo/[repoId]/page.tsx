'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { z } from 'zod';
import { useQuery } from '@tanstack/react-query';
import RepoDetail from '@/components/features/repo/RepoDetail';
import { getRepositoryById } from '@/services/repoService';
import { Spin } from 'antd';

const ParamsSchema = z.object({ repoId: z.string() });

export default function RepoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const parse = ParamsSchema.safeParse(params);

  if (!parse.success) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Invalid Repository ID
          </h2>
          <button
            onClick={() => router.push('/repo')}
            className="text-blue-600 hover:text-blue-700"
          >
            Back to Repositories
          </button>
        </div>
      </div>
    );
  }

  const repoId = parse.data.repoId;

  // Fetch repository details
  const {
    data: repoDetail,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: () => getRepositoryById(repoId),
  });

  const handleBack = () => {
    router.push('/repo');
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Spin size="large" />
      </div>
    );
  }

  if (error || !repoDetail?.repository) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Repository Not Found
          </h2>
          <p className="text-gray-600 mb-4">
            The repository you're looking for doesn't exist or you don't have
            access to it.
          </p>
          <button
            onClick={handleBack}
            className="text-blue-600 hover:text-blue-700"
          >
            Back to Repositories
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full">
      <RepoDetail repo={repoDetail.repository} onBack={handleBack} />
    </div>
  );
}
