'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import RepoList from '@/components/features/repo/RepoList';
import type { Repository } from '@/services/repoService';

export default function RepoListPage() {
  const router = useRouter();

  const handleRepoClick = (repo: Repository) => {
    router.push(`/repo/${repo.repo_id}`);
  };

  return (
    <div className="p-6 h-full">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            My Repositories
          </h1>
          <p className="text-gray-600">
            View and explore your analyzed repositories
          </p>
        </div>
        <RepoList onRepoClick={handleRepoClick} />
      </div>
    </div>
  );
}

