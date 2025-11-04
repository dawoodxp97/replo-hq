'use client';

import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Statistic,
  Progress,
  Tag,
  Empty,
  Spin,
  Alert,
  Typography,
  Space,
  Divider,
} from 'antd';
import {
  CheckCircleOutlined,
  TrophyOutlined,
  BookOutlined,
  StarOutlined,
  CalendarOutlined,
  RocketOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import apiClient from '@/lib/apiClient';
import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import Link from 'next/link';

const { Title, Text } = Typography;

// Define the comprehensive progress payload from the API
interface ModuleProgressDetail {
  progress_id: string;
  module_id: string;
  module_title: string;
  module_order_index: number;
  tutorial_id: string;
  tutorial_title: string;
  tutorial_level: string;
  completed_at: string;
  quiz_score: number | null;
}

interface TutorialProgressSummary {
  tutorial_id: string;
  tutorial_title: string;
  tutorial_level: string;
  total_modules: number;
  completed_modules: number;
  progress_percentage: number;
  average_quiz_score: number | null;
  last_completed_at: string | null;
}

interface UserProgressStats {
  total_modules_completed: number;
  total_quizzes_attempted: number;
  total_quizzes_correct: number;
  average_quiz_score: number;
  total_tutorials_with_progress: number;
  last_activity_at: string | null;
}

interface UserProgressResponse {
  user_id: string;
  stats: UserProgressStats;
  progress: ModuleProgressDetail[];
  tutorials: TutorialProgressSummary[];
}

const COLORS = {
  primary: '#6366f1',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  gradient1: '#667eea',
  gradient2: '#764ba2',
  gradient3: '#f093fb',
  gradient4: '#4facfe',
};

const getLevelColor = (level: string) => {
  const levelLower = level.toLowerCase();
  if (levelLower === 'beginner') return COLORS.success;
  if (levelLower === 'intermediate') return COLORS.warning;
  if (levelLower === 'advanced') return COLORS.danger;
  return COLORS.primary;
};

const getLevelTagColor = (level: string) => {
  const levelLower = level.toLowerCase();
  if (levelLower === 'beginner') return 'green';
  if (levelLower === 'intermediate') return 'orange';
  if (levelLower === 'advanced') return 'red';
  return 'blue';
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatDateShort = (dateString: string | null) => {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

export default function ProgressTracker() {
  const { data, error, isLoading } = useQuery<UserProgressResponse>({
    queryKey: ['progress'],
    queryFn: async () => {
      const response: any = await apiClient.get(API_ENDPOINTS.PROGRESS_GET);
      return (response?.data ?? response) as UserProgressResponse;
    },
    refetchOnWindowFocus: true,
  });

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!data?.tutorials) return [];

    return data.tutorials.map(tutorial => ({
      name:
        tutorial.tutorial_title.length > 20
          ? tutorial.tutorial_title.substring(0, 20) + '...'
          : tutorial.tutorial_title,
      fullName: tutorial.tutorial_title,
      completed: tutorial.completed_modules,
      total: tutorial.total_modules,
      progress: tutorial.progress_percentage,
    }));
  }, [data?.tutorials]);

  const pieData = useMemo(() => {
    if (!data?.stats) return [];

    const completed = data.stats.total_modules_completed;
    const attempted = data.stats.total_quizzes_attempted;
    const correct = data.stats.total_quizzes_correct;

    return [
      { name: 'Completed Modules', value: completed, color: COLORS.success },
      { name: 'Quizzes Attempted', value: attempted, color: COLORS.warning },
      { name: 'Correct Answers', value: correct, color: COLORS.primary },
    ];
  }, [data?.stats]);

  const levelDistribution = useMemo(() => {
    if (!data?.tutorials) return [];

    const levels: Record<string, number> = {};
    data.tutorials.forEach(tutorial => {
      const level = tutorial.tutorial_level.toLowerCase();
      levels[level] = (levels[level] || 0) + 1;
    });

    return Object.entries(levels).map(([level, count]) => ({
      name: level.charAt(0).toUpperCase() + level.slice(1),
      value: count,
      color: getLevelColor(level),
    }));
  }, [data?.tutorials]);

  const recentActivity = useMemo(() => {
    if (!data?.progress) return [];
    return data.progress.slice(0, 10);
  }, [data?.progress]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert
          message="Failed to load progress"
          description="There was an error loading your progress data. Please try again later."
          type="error"
          showIcon
        />
      </div>
    );
  }

  const progressData: UserProgressResponse = data ?? {
    user_id: '',
    stats: {
      total_modules_completed: 0,
      total_quizzes_attempted: 0,
      total_quizzes_correct: 0,
      average_quiz_score: 0,
      total_tutorials_with_progress: 0,
      last_activity_at: null,
    },
    progress: [],
    tutorials: [],
  };

  const { stats, tutorials, progress } = progressData;

  const hasNoProgress = stats.total_modules_completed === 0;

  return (
    <div className="!max-w-[calc(100vw-220px)] !h-[calc(100vh-90px)] overflow-auto bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6 flex flex-col gap-4">
        {/* Header */}
        <div className="">
          <Title
            level={1}
            className="!mb-2 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
          >
            <RocketOutlined className="mr-3" />
            Your Learning Progress
          </Title>
          <Text type="secondary" className="text-lg">
            Track your journey through interactive tutorials
          </Text>
        </div>

        {hasNoProgress ? (
          <Card className="shadow-lg border-0">
            <Empty
              description={
                <span className="text-gray-500">
                  You haven't completed any modules yet. Start learning to see
                  your progress here!
                </span>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Link href="/dashboard">
                <button className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                  Browse Tutorials
                </button>
              </Link>
            </Empty>
          </Card>
        ) : (
          <>
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <Card className="shadow-lg border-0 hover:shadow-xl transition-shadow bg-gradient-to-br from-indigo-500 to-purple-600">
                <Statistic
                  title={
                    <span className=" font-medium">Modules Completed</span>
                  }
                  value={stats.total_modules_completed}
                  prefix={
                    <span
                      style={{
                        background:
                          'linear-gradient(135deg, #a855f7 0%, #3b82f6 50%, #06b6d4 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        display: 'inline-block',
                      }}
                    >
                      <CheckCircleOutlined />
                    </span>
                  }
                  valueStyle={{
                    background:
                      'linear-gradient(135deg, #a855f7 0%, #3b82f6 50%, #06b6d4 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    fontSize: '2rem',
                    fontWeight: 'bold',
                  }}
                />
              </Card>

              <Card className="shadow-lg border-0 hover:shadow-xl transition-shadow bg-gradient-to-br from-green-500 to-emerald-600">
                <Statistic
                  title={<span className=" font-medium">Quiz Accuracy</span>}
                  value={stats.average_quiz_score}
                  suffix="%"
                  prefix={
                    <span
                      style={{
                        background:
                          'linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #06b6d4 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        display: 'inline-block',
                      }}
                    >
                      <TrophyOutlined />
                    </span>
                  }
                  valueStyle={{
                    background:
                      'linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #06b6d4 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    fontSize: '2rem',
                    fontWeight: 'bold',
                  }}
                />
              </Card>

              <Card className="shadow-lg border-0 hover:shadow-xl transition-shadow bg-gradient-to-br from-blue-500 to-cyan-600">
                <Statistic
                  title={<span className=" font-medium">Active Tutorials</span>}
                  value={stats.total_tutorials_with_progress}
                  prefix={
                    <span
                      style={{
                        background:
                          'linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #8b5cf6 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        display: 'inline-block',
                      }}
                    >
                      <BookOutlined />
                    </span>
                  }
                  valueStyle={{
                    background:
                      'linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #8b5cf6 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    fontSize: '2rem',
                    fontWeight: 'bold',
                  }}
                />
              </Card>

              <Card className="shadow-lg border-0 hover:shadow-xl transition-shadow bg-gradient-to-br from-amber-500 to-orange-600">
                <Statistic
                  title={<span className=" font-medium">Quizzes Correct</span>}
                  value={stats.total_quizzes_correct}
                  suffix={`/ ${stats.total_quizzes_attempted}`}
                  prefix={
                    <span
                      style={{
                        background:
                          'linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #ec4899 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        display: 'inline-block',
                      }}
                    >
                      <StarOutlined />
                    </span>
                  }
                  valueStyle={{
                    background:
                      'linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #ec4899 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    fontSize: '2rem',
                    fontWeight: 'bold',
                  }}
                />
              </Card>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Progress by Tutorial */}
              <Card
                title={
                  <span className="flex items-center gap-2">
                    <ThunderboltOutlined className="text-indigo-600" />
                    Progress by Tutorial
                  </span>
                }
                className="shadow-lg border-0"
              >
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        tick={{ fill: '#6b7280', fontSize: 12 }}
                      />
                      <YAxis tick={{ fill: '#6b7280' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#fff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                        }}
                        formatter={(value: any, name: string) => {
                          if (name === 'progress')
                            return [`${value.toFixed(1)}%`, 'Progress'];
                          return [value, name];
                        }}
                      />
                      <Legend />
                      <Bar
                        dataKey="completed"
                        fill={COLORS.primary}
                        name="Completed Modules"
                        radius={[8, 8, 0, 0]}
                      />
                      <Bar
                        dataKey="total"
                        fill={COLORS.warning}
                        name="Total Modules"
                        radius={[8, 8, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty description="No tutorial data available" />
                )}
              </Card>

              {/* Activity Distribution */}
              <Card
                title={
                  <span className="flex items-center gap-2">
                    <BookOutlined className="text-purple-600" />
                    Level Distribution
                  </span>
                }
                className="shadow-lg border-0"
              >
                {levelDistribution.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={levelDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(props: any) => {
                          const percent = props.percent || 0;
                          const name = props.name || '';
                          return `${name}: ${(percent * 100).toFixed(0)}%`;
                        }}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {levelDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty description="No level data available" />
                )}
              </Card>
            </div>

            {/* Tutorial Progress Breakdown */}
            <Card
              title={
                <span className="flex items-center gap-2">
                  <BookOutlined className="text-indigo-600" />
                  Tutorial Progress Breakdown
                </span>
              }
              className="shadow-lg border-0"
            >
              {tutorials.length > 0 ? (
                <div className="space-y-4">
                  {tutorials.map(tutorial => (
                    <div
                      key={tutorial.tutorial_id}
                      className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow bg-white"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Title level={5} className="!mb-0">
                              {tutorial.tutorial_title}
                            </Title>
                            <Tag
                              color={getLevelTagColor(tutorial.tutorial_level)}
                            >
                              {tutorial.tutorial_level}
                            </Tag>
                          </div>
                          <Text type="secondary" className="text-sm">
                            {tutorial.completed_modules} of{' '}
                            {tutorial.total_modules} modules completed
                            {tutorial.average_quiz_score !== null && (
                              <span className="ml-2">
                                • Quiz Score:{' '}
                                {tutorial.average_quiz_score.toFixed(1)}%
                              </span>
                            )}
                          </Text>
                        </div>
                        <Link href={`/tutorial/${tutorial.tutorial_id}`}>
                          <button className="px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors text-sm font-medium">
                            Continue
                          </button>
                        </Link>
                      </div>
                      <Progress
                        percent={tutorial.progress_percentage}
                        strokeColor={{
                          '0%': COLORS.gradient1,
                          '100%': COLORS.gradient2,
                        }}
                        showInfo={true}
                        format={percent =>
                          `${((percent as number) || 0).toFixed(1)}%`
                        }
                      />
                      {tutorial.last_completed_at && (
                        <Text type="secondary" className="text-xs mt-2 block">
                          <CalendarOutlined className="mr-1" />
                          Last activity:{' '}
                          {formatDateShort(tutorial.last_completed_at)}
                        </Text>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <Empty description="No tutorial progress available" />
              )}
            </Card>

            {/* Recent Activity */}
            {recentActivity.length > 0 && (
              <Card
                title={
                  <span className="flex items-center gap-2">
                    <CalendarOutlined className="text-green-600" />
                    Recent Activity
                  </span>
                }
                className="shadow-lg border-0"
              >
                <div className="space-y-3">
                  {recentActivity.map(item => (
                    <div
                      key={item.progress_id}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <CheckCircleOutlined className="text-green-500 text-xl" />
                        <div className="flex-1">
                          <Text strong>{item.module_title}</Text>
                          <div className="flex items-center gap-2 mt-1">
                            <Text type="secondary" className="text-sm">
                              {item.tutorial_title}
                            </Text>
                            <Tag color={getLevelTagColor(item.tutorial_level)}>
                              {item.tutorial_level}
                            </Tag>
                            {item.quiz_score !== null && (
                              <Tag
                                color={
                                  item.quiz_score === 1 ? 'success' : 'error'
                                }
                              >
                                Quiz: {item.quiz_score === 1 ? '✓' : '✗'}
                              </Tag>
                            )}
                          </div>
                        </div>
                      </div>
                      <Text
                        type="secondary"
                        className="text-sm whitespace-nowrap"
                      >
                        {formatDateShort(item.completed_at)}
                      </Text>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Last Activity Footer */}
            {stats.last_activity_at && (
              <Card className="shadow-lg border-0 bg-gradient-to-r from-indigo-50 to-purple-50">
                <div className="flex items-center justify-center gap-2 text-gray-600">
                  <CalendarOutlined />
                  <Text>
                    Last activity:{' '}
                    <strong>{formatDate(stats.last_activity_at)}</strong>
                  </Text>
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}
