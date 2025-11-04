'use client';

import { memo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Tag,
  Input,
  Select,
  Progress,
  Empty,
  Spin,
} from 'antd';
import { Search, SlidersHorizontal, BookOpen, Clock, Play } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { getAllTutorials, TutorialListItem } from '@/services/tutorialService';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import Loader from '@/components/ui/loader/Loader';
import Error from '@/components/ui/error/Error';

type Tutorial = TutorialListItem;

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

const getEstimatedTime = (moduleCount: number): string => {
  // Estimate ~30 minutes per module
  const hours = Math.ceil((moduleCount * 30) / 60);
  return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
};

const getImageUrl = (repoUrl: string | null, level: string): string => {
  // Generate a deterministic image based on repo URL or level
  if (repoUrl) {
    const repoName = repoUrl.split('/').pop()?.replace('.git', '') || '';
    // Use a hash-like approach to get consistent images
    const seed = repoName.length + level.length;
    const images = [
      'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=400',
      'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=400',
      'https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=400',
      'https://images.unsplash.com/photo-1618477388954-7852f32655ec?w=400',
      'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400',
      'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400',
    ];
    return images[seed % images.length];
  }
  return 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=400';
};

const MyTutorials = (props: {}) => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState<string>('all');
  const [filterProgress, setFilterProgress] = useState<string>('all');

  const {
    data: tutorials,
    isLoading,
    error,
  } = useQuery<Tutorial[]>({
    queryKey: ['tutorials'],
    queryFn: async () => {
      return await getAllTutorials();
    },
  });

  const filteredTutorials =
    tutorials?.filter((tutorial: Tutorial) => {
      const matchesSearch =
        !searchQuery ||
        tutorial.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tutorial.overview?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tutorial.repo_name?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesDifficulty =
        filterDifficulty === 'all' ||
        tutorial.level.toLowerCase() === filterDifficulty.toLowerCase();

      const matchesProgress =
        filterProgress === 'all' ||
        (filterProgress === 'not-started' &&
          tutorial.progress_percentage === 0) ||
        (filterProgress === 'in-progress' &&
          tutorial.progress_percentage > 0 &&
          tutorial.progress_percentage < 100) ||
        (filterProgress === 'completed' &&
          tutorial.progress_percentage === 100);

      return matchesSearch && matchesDifficulty && matchesProgress;
    }) || [];

  const handleCardClick = (tutorialId: string) => {
    router.push(`/tutorial/${tutorialId}`);
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

  return (
    <div className="max-w-[calc(100vw-220px)] p-6 h-[calc(100vh-90px)] overflow-auto flex flex-col gap-6">
      {/* Header */}
      <div className="">
        <div className="flex items-center gap-3 mb-3">
          <BookOpen className="w-6 h-6 text-indigo-500 animate-pulse" />
          <h1 className="text-3xl !mb-0 font-bold bg-gradient-to-r from-slate-900 via-indigo-900 to-purple-900 bg-clip-text text-transparent">
            My Tutorials
          </h1>
        </div>
        <p className="text-slate-600 !mb-0">
          Continue learning or explore new tutorials
        </p>
      </div>

      {/* Filters */}
      <Card className="border-slate-200/50 bg-white/90 backdrop-blur-sm mb-6 shadow-sm">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Input
              size="large"
              placeholder="Search tutorials..."
              prefix={<Search className="w-4 h-4 text-slate-400" />}
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="rounded-lg"
            />
          </Col>
          <Col xs={12} md={6}>
            <Select
              size="large"
              value={filterDifficulty}
              onChange={setFilterDifficulty}
              className="w-full"
              suffixIcon={<SlidersHorizontal className="w-4 h-4" />}
            >
              <Select.Option value="all">All Levels</Select.Option>
              <Select.Option value="beginner">Beginner</Select.Option>
              <Select.Option value="intermediate">Intermediate</Select.Option>
              <Select.Option value="advanced">Advanced</Select.Option>
            </Select>
          </Col>
          <Col xs={12} md={6}>
            <Select
              size="large"
              value={filterProgress}
              onChange={setFilterProgress}
              className="w-full"
            >
              <Select.Option value="all">All Progress</Select.Option>
              <Select.Option value="not-started">Not Started</Select.Option>
              <Select.Option value="in-progress">In Progress</Select.Option>
              <Select.Option value="completed">Completed</Select.Option>
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
                  height: '470px',
                  display: 'flex',
                  flexDirection: 'column',
                }}
                bodyStyle={{
                  flex: 1,
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
                cover={
                  <div className="relative h-48 overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200">
                    <ImageWithFallback
                      src={getImageUrl(tutorial.repo_url, tutorial.level)}
                      alt={tutorial.title}
                      className="group-hover:scale-110 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="absolute top-3 right-3">
                      <Tag color={getDifficultyColor(tutorial.level)}>
                        {getDifficultyLabel(tutorial.level)}
                      </Tag>
                    </div>
                    <div className="absolute bottom-3 left-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <div className="flex items-center gap-2 text-white">
                        <Play className="w-4 h-4" />
                        <span className="text-sm font-medium">
                          Continue Learning
                        </span>
                      </div>
                    </div>
                  </div>
                }
                onClick={() => handleCardClick(tutorial.tutorial_id)}
              >
                <div className="space-y-3 flex flex-col h-full justify-between">
                  <div className="mb-1">
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
                      <BookOpen className="w-4 h-4" />
                      {tutorial.module_count}{' '}
                      {tutorial.module_count === 1 ? 'module' : 'modules'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {getEstimatedTime(tutorial.module_count)}
                    </span>
                  </div>

                  <div className="space-y-2 pt-2 border-t border-slate-200">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Progress</span>
                      <span className="font-medium text-slate-900">
                        {tutorial.completed_modules}/{tutorial.module_count}{' '}
                        modules
                      </span>
                    </div>
                    <Progress
                      percent={tutorial.progress_percentage}
                      strokeColor={{
                        '0%': '#6366f1',
                        '100%': '#a855f7',
                      }}
                      size="small"
                      showInfo={false}
                    />
                    <div className="text-xs text-slate-500 text-right">
                      {tutorial.progress_percentage}% complete
                    </div>
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
              searchQuery ||
              filterDifficulty !== 'all' ||
              filterProgress !== 'all'
                ? 'No tutorials match your filters. Try adjusting your search criteria.'
                : "You haven't generated any tutorials yet. Start by generating one from the dashboard!"
            }
          />
        </Card>
      )}

      {/* Stats Footer */}
      {filteredTutorials.length > 0 && tutorials && tutorials.length > 0 && (
        <div className=" border-t border-slate-200 h-[77px]">
          <p className="text-slate-500 text-sm">
            Showing {filteredTutorials.length} of {tutorials.length} tutorial
            {tutorials.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
};

export default memo(MyTutorials);
