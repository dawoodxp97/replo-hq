'use client';

import { memo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Typography, Tag, Input, Empty, Spin, Space } from 'antd';
import {
  SearchOutlined,
  BookOutlined,
  CalendarOutlined,
  PlayCircleOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { getAllTutorials, TutorialListItem } from '@/services/tutorialService';
import type { SearchProps } from 'antd/es/input/Search';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

type Tutorial = TutorialListItem;

const levelColors: Record<string, { color: string; icon: React.ReactNode }> = {
  BEGINNER: { color: 'green', icon: <RocketOutlined /> },
  INTERMEDIATE: { color: 'orange', icon: <BookOutlined /> },
  ADVANCED: { color: 'red', icon: <RocketOutlined /> },
};

const getLevelColor = (level: string) => {
  return levelColors[level.toUpperCase()]?.color || 'default';
};

const getLevelIcon = (level: string) => {
  return levelColors[level.toUpperCase()]?.icon || <BookOutlined />;
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const MyTutorials = (props: {}) => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');

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
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        tutorial.title.toLowerCase().includes(query) ||
        tutorial.overview?.toLowerCase().includes(query) ||
        tutorial.level.toLowerCase().includes(query)
      );
    }) || [];

  const handleCardClick = (tutorialId: string) => {
    router.push(`/tutorial/${tutorialId}`);
  };

  const onSearch: SearchProps['onSearch'] = value => {
    setSearchQuery(value);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-96">
        <Empty
          description="Failed to load tutorials. Please try again later."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    );
  }

  return (
    <div className="w-full h-full p-6 md:p-8 bg-gradient-to-br from-gray-50 via-white to-blue-50 min-h-screen">
      {/* Header Section */}
      <div className="mb-8">
        <Title
          level={2}
          className="!mb-2 !text-3xl md:!text-4xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
        >
          My Tutorials
        </Title>
        <Text className="text-gray-600 text-base">
          Explore and continue your learning journey with AI-generated tutorials
        </Text>
      </div>

      {/* Search Section */}
      <div className="mb-6">
        <Search
          placeholder="Search tutorials by title, description, or level..."
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          onSearch={onSearch}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-2xl"
          style={{
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          }}
        />
      </div>

      {/* Tutorials Grid */}
      {filteredTutorials.length === 0 ? (
        <div className="mt-12">
          <Empty
            description={
              searchQuery
                ? 'No tutorials match your search. Try a different query.'
                : "You haven't generated any tutorials yet. Start by generating one from the dashboard!"
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTutorials.map((tutorial: Tutorial) => (
            <Card
              key={tutorial.tutorial_id}
              hoverable
              onClick={() => handleCardClick(tutorial.tutorial_id)}
              className="!rounded-2xl !border-none shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 bg-white/80 backdrop-blur-sm"
              style={{
                background:
                  'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(249,250,251,0.9) 100%)',
                border: '1px solid rgba(229, 231, 235, 0.8)',
              }}
              bodyStyle={{ padding: '24px' }}
            >
              <div className="flex flex-col h-full">
                {/* Header with Level Badge */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <Title
                      level={4}
                      className="!mb-2 !text-xl !font-bold !text-gray-800 line-clamp-2"
                      ellipsis={{ tooltip: tutorial.title }}
                    >
                      {tutorial.title}
                    </Title>
                  </div>
                  <Tag
                    color={getLevelColor(tutorial.level)}
                    icon={getLevelIcon(tutorial.level)}
                    className="!m-0 !px-3 !py-1 !rounded-full !font-semibold !text-xs"
                    style={{
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      marginLeft: '8px',
                    }}
                  >
                    {tutorial.level}
                  </Tag>
                </div>

                {/* Overview */}
                {tutorial.overview && (
                  <Paragraph
                    className="!mb-4 !text-gray-600 !text-sm line-clamp-3 flex-1"
                    ellipsis={{ rows: 3, expandable: false }}
                  >
                    {tutorial.overview}
                  </Paragraph>
                )}

                {/* Footer Stats */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                  <Space size="small" className="text-gray-500">
                    <BookOutlined className="text-sm" />
                    <Text className="!text-xs !text-gray-500">
                      {tutorial.module_count}{' '}
                      {tutorial.module_count === 1 ? 'module' : 'modules'}
                    </Text>
                  </Space>
                  <Space size="small" className="text-gray-500">
                    <CalendarOutlined className="text-sm" />
                    <Text className="!text-xs !text-gray-500">
                      {formatDate(tutorial.generated_at)}
                    </Text>
                  </Space>
                </div>

                {/* Action Indicator */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-center text-blue-600 hover:text-blue-700 transition-colors">
                    <PlayCircleOutlined className="mr-2" />
                    <Text className="!text-sm !font-medium">
                      Continue Learning
                    </Text>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Stats Footer */}
      {filteredTutorials.length > 0 && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <Text className="text-gray-500 text-sm">
            Showing {filteredTutorials.length} of {tutorials?.length || 0}{' '}
            tutorial{tutorials?.length !== 1 ? 's' : ''}
          </Text>
        </div>
      )}
    </div>
  );
};

export default memo(MyTutorials);
