'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Button,
  Card,
  Col,
  Empty,
  Input,
  message,
  Row,
  Select,
  Tag,
  Typography,
} from 'antd';
import { ArrowRight, BookOpen, Edit, Files, Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import apiClient from '@/lib/apiClient';

import TutorialEditor from '@/components/author/TutorialEditor';
import Error from '@/components/ui/error/Error';
import Loader from '@/components/ui/loader/Loader';

interface TutorialListItem {
  tutorial_id: string;
  title: string;
  level: string;
  overview: string | null;
  generated_at: string;
  repo_name: string | null;
  repo_url: string | null;
  module_count: number;
}

const getDifficultyColor = (difficulty: string) => {
  const colors: Record<string, string> = {
    BEGINNER: 'green',
    INTERMEDIATE: 'blue',
    ADVANCED: 'purple',
  };
  return colors[difficulty.toUpperCase()] || 'default';
};

const getDifficultyLabel = (difficulty: string) => {
  const labels: Record<string, string> = {
    BEGINNER: 'Beginner',
    INTERMEDIATE: 'Intermediate',
    ADVANCED: 'Advanced',
  };
  return labels[difficulty.toUpperCase()] || difficulty;
};

export default function Authoring() {
  const router = useRouter();
  const [selectedTutorialId, setSelectedTutorialId] = useState<string | null>(
    null
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState<string>('all');

  const {
    data: tutorials,
    isLoading,
    error,
  } = useQuery<TutorialListItem[]>({
    queryKey: ['author-tutorials'],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.AUTHOR_DASHBOARD);
    },
  });

  const filteredTutorials =
    tutorials?.filter(tutorial => {
      const matchesSearch =
        !searchQuery ||
        tutorial.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tutorial.overview?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tutorial.repo_name?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesLevel =
        filterLevel === 'all' ||
        tutorial.level.toLowerCase() === filterLevel.toLowerCase();

      return matchesSearch && matchesLevel;
    }) || [];

  const handleTutorialSelect = (tutorialId: string) => {
    setSelectedTutorialId(tutorialId);
  };

  const handleBackToList = () => {
    setSelectedTutorialId(null);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader type="dots" size="lg" message="Loading tutorials..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-full">
        <Error
          title="Error loading tutorials"
          variant="full"
          message="Failed to load tutorials. Please try again later."
          error={error}
        />
      </div>
    );
  }

  // Show editor if tutorial is selected
  if (selectedTutorialId) {
    return (
      <div className="w-full h-full flex flex-col">
        <div className="p-4 border-b bg-white">
          <Button
            type="link"
            icon={<ArrowRight className="w-4 h-4 rotate-180" />}
            onClick={handleBackToList}
            className="mb-2 !p-0"
          >
            Back to Tutorials
          </Button>
          <Typography.Title level={3} className="!mb-0 !mt-0">
            Edit Tutorial
          </Typography.Title>
        </div>
        <div className="flex-1 overflow-hidden">
          <TutorialEditor tutorialId={selectedTutorialId} />
        </div>
      </div>
    );
  }

  // Show tutorial list
  return (
    <div className="max-w-[calc(100vw-220px)] p-6 h-[calc(100vh-90px)] overflow-auto flex flex-col gap-6 justify-between">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <Edit className="w-6 h-6 text-indigo-500" />
          <h1 className="text-3xl !mb-0 font-bold bg-gradient-to-r from-slate-900 via-indigo-900 to-purple-900 bg-clip-text text-transparent">
            Authoring
          </h1>
        </div>
        <p className="text-slate-600 !mb-0">
          Select a tutorial to edit its content, modules, and quizzes
        </p>
      </div>

      {/* Filters */}
      <Card className="border-slate-200/50 bg-white/90 backdrop-blur-sm mb-6 shadow-sm">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={16}>
            <Input
              size="large"
              placeholder="Search tutorials..."
              prefix={<Search className="w-4 h-4 text-slate-400" />}
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="rounded-lg"
            />
          </Col>
          <Col xs={24} md={8}>
            <Select
              size="large"
              value={filterLevel}
              onChange={setFilterLevel}
              className="w-full"
            >
              <Select.Option value="all">All Levels</Select.Option>
              <Select.Option value="beginner">Beginner</Select.Option>
              <Select.Option value="intermediate">Intermediate</Select.Option>
              <Select.Option value="advanced">Advanced</Select.Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Tutorials Grid */}
      {filteredTutorials.length > 0 ? (
        <Row gutter={[16, 16]}>
          {filteredTutorials.map(tutorial => (
            <Col key={tutorial.tutorial_id} xs={24} sm={12} md={8} lg={8}>
              <Card
                className="border-slate-200/50 hover:shadow-xl transition-all duration-300 hover:border-indigo-300/50 cursor-pointer bg-white/90 backdrop-blur-sm group hover:-translate-y-1"
                style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                }}
                bodyStyle={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                }}
                onClick={() => handleTutorialSelect(tutorial.tutorial_id)}
              >
                <div className="space-y-3 flex flex-col h-full justify-between">
                  <div className="mb-1">
                    <div className="flex items-center justify-between mb-2">
                      <Tag color={getDifficultyColor(tutorial.level)}>
                        {getDifficultyLabel(tutorial.level)}
                      </Tag>
                      <Edit className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                    </div>
                    <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors mb-1 line-clamp-2">
                      {tutorial.title}
                    </h3>
                    <p className="text-sm text-slate-600 line-clamp-1 !mb-0">
                      {tutorial.repo_name ||
                        tutorial.repo_url?.replace('https://github.com/', '') ||
                        'Repository'}
                    </p>
                  </div>

                  {tutorial.overview && (
                    <p className="text-sm text-slate-600 line-clamp-2 !mb-0">
                      {tutorial.overview}
                    </p>
                  )}

                  <div className="flex items-center gap-4 text-sm text-slate-600 mt-1">
                    <span className="flex items-center gap-1">
                      <Files className="w-4 h-4" />
                      {tutorial.module_count}{' '}
                      {tutorial.module_count === 1 ? 'module' : 'modules'}
                    </span>
                  </div>

                  <div className="pt-2 border-t border-slate-200">
                    <Button
                      type="primary"
                      block
                      icon={<Edit className="w-4 h-4" />}
                      className="mt-2 !bg-gradient-to-r !from-indigo-500 !via-purple-500 !to-pink-500 !text-white shadow-lg !scale-105 hover:!scale-105 hover:!bg-gradient-to-r hover:!from-indigo-600 hover:!via-purple-600 hover:!to-pink-600"
                      onClick={e => {
                        e.stopPropagation();
                        handleTutorialSelect(tutorial.tutorial_id);
                      }}
                    >
                      Edit Tutorial
                    </Button>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Card className="border-slate-200/60 bg-white/80 backdrop-blur-sm">
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              searchQuery || filterLevel !== 'all'
                ? 'No tutorials match your filters. Try adjusting your search criteria.'
                : "You haven't created any tutorials yet. Start by generating one from the dashboard!"
            }
          />
        </Card>
      )}

      {/* Stats Footer */}
      {filteredTutorials.length > 0 && tutorials && tutorials.length > 0 && (
        <div className="border-t border-slate-200 pt-4">
          <p className="text-slate-500 text-sm">
            Showing {filteredTutorials.length} of {tutorials.length} tutorial
            {tutorials.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
}
