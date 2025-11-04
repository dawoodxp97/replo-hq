'use client';

import React, { memo } from 'react';
import { Card, Tag, Spin, Empty } from 'antd';
import { useQuery } from '@tanstack/react-query';
import {
  FolderOpen,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
  Github,
} from 'lucide-react';
import { getRepositories, type Repository } from '@/services/repoService';
import EmptyState from '@/components/ui/empty-state/EmptyState';
import {
  borderGradientDefault,
  borderGradientHover,
  backgroundGradientDefault,
  backgroundGradientHover,
  boxShadows,
} from '@/constants/gradientColors';

interface RepoListProps {
  onRepoClick: (repo: Repository) => void;
}

const getStatusColor = (status: string) => {
  const upperStatus = status.toUpperCase();
  if (upperStatus === 'COMPLETED') return 'success';
  if (upperStatus === 'ANALYZING' || upperStatus === 'PENDING') return 'processing';
  if (upperStatus === 'FAILED') return 'error';
  return 'default';
};

const getStatusIcon = (status: string) => {
  const upperStatus = status.toUpperCase();
  if (upperStatus === 'COMPLETED') return <CheckCircle className="w-4 h-4" />;
  if (upperStatus === 'ANALYZING') return <Loader2 className="w-4 h-4 animate-spin" />;
  if (upperStatus === 'PENDING') return <Clock className="w-4 h-4" />;
  if (upperStatus === 'FAILED') return <XCircle className="w-4 h-4" />;
  return <FolderOpen className="w-4 h-4" />;
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

const RepoList = ({ onRepoClick }: RepoListProps) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['repositories'],
    queryFn: getRepositories,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Empty
        description="Failed to load repositories"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  const repositories = data?.repositories || [];

  if (repositories.length === 0) {
    return (
      <EmptyState
        variant="illustration"
        title="No Repositories Yet"
        description="Start by adding a GitHub repository to analyze and generate tutorials from."
        primaryAction={{
          label: 'Add Repository',
          onClick: () => {
            // Navigate to dashboard or add repo modal
            window.location.href = '/dashboard';
          },
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {repositories.map((repo) => (
          <Card
            key={repo.repo_id}
            hoverable
            onClick={() => onRepoClick(repo)}
            className="cursor-pointer transition-all duration-300"
            style={{
              borderRadius: '12px',
              border: 'none',
              background: backgroundGradientDefault,
              boxShadow: boxShadows.default,
            }}
            bodyStyle={{ padding: '20px' }}
          >
            <div className="space-y-3">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <div className="flex-shrink-0 p-2 rounded-lg bg-gradient-to-br from-blue-400/20 to-purple-400/20">
                    <Github className="w-5 h-5 text-purple-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate text-base">
                      {repo.name || 'Unnamed Repository'}
                    </h3>
                    <p className="text-xs text-gray-500 truncate mt-0.5">
                      {repo.github_url.split('/').slice(-2).join('/')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Description */}
              {repo.description && (
                <p className="text-sm text-gray-600 line-clamp-2">
                  {repo.description}
                </p>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between pt-2 border-t border-gray-200/50">
                <Tag
                  color={getStatusColor(repo.status)}
                  icon={getStatusIcon(repo.status)}
                  className="flex items-center gap-1"
                >
                  {repo.status}
                </Tag>
                <span className="text-xs text-gray-500">
                  {formatDate(repo.created_at)}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <style jsx global>{`
        .ant-card {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        .ant-card:hover {
          transform: translateY(-4px) !important;
          box-shadow: ${boxShadows.hover} !important;
          background: ${backgroundGradientHover} !important;
        }
      `}</style>
    </div>
  );
};

export default memo(RepoList);

