'use client';

import { memo } from 'react';
import {
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd';
import {
  Activity,
  BookOpen,
  Calendar,
  CheckCircle,
  CheckCircle2,
  Circle,
  Clock,
  Flame,
  GitBranch,
  Loader2,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';

import { API_ENDPOINTS } from '@/constants/apiEndpoints';
import apiClient from '@/lib/apiClient';
import { useGlobalStore } from '@/store/useGlobalStore';

import Loader from '@/components/ui/loader/Loader';

const { Title, Text } = Typography;
const GRADIENT_COLORS = {
  blue: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  purple: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  green: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  orange: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  pink: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  indigo: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
};

const STAT_CARD_COLORS = [
  { gradient: GRADIENT_COLORS.blue, icon: '#667eea' },
  { gradient: GRADIENT_COLORS.purple, icon: '#f093fb' },
  { gradient: GRADIENT_COLORS.green, icon: '#4facfe' },
  { gradient: GRADIENT_COLORS.orange, icon: '#fa709a' },
  { gradient: GRADIENT_COLORS.indigo, icon: '#764ba2' },
];

const PIE_COLORS = ['#667eea', '#f093fb', '#00f2fe'];

interface DashboardStats {
  tutorials_generated: number;
  learning_hours: number;
  current_streak: number;
  completed_tutorials: number;
  total_hours_this_week: number;
}

interface WeeklyActivity {
  day: string;
  hour: number;
  value: number;
}

interface TutorialStatus {
  completed: number;
  in_progress: number;
  not_started: number;
}

interface RecentActivityItem {
  repo_id: string;
  repo_name: string;
  repo_url: string;
  status: string;
  generation_progress?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  tutorial_id?: string;
}

const getStatusColor = (status: string): string => {
  const statusMap: Record<string, string> = {
    COMPLETED: 'success',
    PROCESSING: 'processing',
    GENERATING: 'processing',
    ANALYZING: 'processing',
    CLONING: 'processing',
    PENDING: 'warning',
    FAILED: 'error',
  };
  return statusMap[status] || 'default';
};

const getStatusIcon = (status: string) => {
  if (status === 'COMPLETED') return <CheckCircle2 className="w-4 h-4" />;
  if (status === 'FAILED') return <XCircle className="w-4 h-4" />;
  if (['PROCESSING', 'GENERATING', 'ANALYZING', 'CLONING'].includes(status))
    return <Loader2 className="w-4 h-4 animate-spin" />;
  return <Circle className="w-4 h-4" />;
};

const StatCard = ({
  title,
  value,
  suffix,
  icon: Icon,
  color,
  index,
}: {
  title: string;
  value: string | number;
  suffix?: string;
  icon: any;
  color: { gradient: string; icon: string };
  index: number;
}) => (
  <Card
    className="h-full border-0 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
    bodyStyle={{ padding: '24px' }}
    style={{
      background: color.gradient,
      borderRadius: '16px',
      overflow: 'hidden',
      position: 'relative',
    }}
  >
    <div className="relative z-10">
      <div className="flex items-start justify-between mb-4">
        <div
          className="p-3 rounded-xl bg-white/20 backdrop-blur-sm"
          style={{ color: color.icon }}
        >
          <Icon className="w-6 h-6 !text-white" />
        </div>
      </div>
      <Statistic
        title={
          <span className="text-white/90 font-medium text-sm">{title}</span>
        }
        value={value}
        suffix={suffix}
        valueStyle={{
          color: 'white',
          fontSize: '28px',
          fontWeight: 'bold',
        }}
      />
    </div>
    <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
  </Card>
);

const Dashboard: React.FC = () => {
  const { user } = useGlobalStore();

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.DASHBOARD_STATS);
    },
  });

  // Fetch weekly activity
  const { data: weeklyActivity, isLoading: weeklyLoading } = useQuery<{
    activities: WeeklyActivity[];
  }>({
    queryKey: ['dashboard-weekly-activity'],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.DASHBOARD_WEEKLY_ACTIVITY);
    },
  });

  // Fetch tutorial status
  const { data: tutorialStatus, isLoading: statusLoading } = useQuery<{
    status: TutorialStatus;
  }>({
    queryKey: ['dashboard-tutorial-status'],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.DASHBOARD_TUTORIAL_STATUS);
    },
  });

  // Fetch recent activity
  const { data: recentActivity, isLoading: recentLoading } = useQuery<{
    activities: RecentActivityItem[];
  }>({
    queryKey: ['dashboard-recent-activity'],
    queryFn: async () => {
      return apiClient.get(API_ENDPOINTS.DASHBOARD_RECENT_ACTIVITY);
    },
  });

  // Process weekly activity data for chart
  const processWeeklyData = () => {
    if (!weeklyActivity?.activities) return [];

    const days = [
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
      'Sunday',
    ];
    const data = days.map(day => {
      const dayActivities = weeklyActivity.activities.filter(
        a => a.day === day
      );
      const totalValue = dayActivities.reduce((sum, a) => sum + a.value, 0);
      return { day: day.substring(0, 3), value: totalValue };
    });

    return data;
  };

  // Process tutorial status for pie chart
  const processTutorialStatusData = () => {
    if (!tutorialStatus?.status) return [];

    const { completed, in_progress, not_started } = tutorialStatus.status;
    return [
      { name: 'Completed', value: completed },
      { name: 'In Progress', value: in_progress },
      { name: 'Not Started', value: not_started },
    ];
  };

  const isLoading =
    statsLoading || weeklyLoading || statusLoading || recentLoading;

  if (isLoading) {
    return (
      <div className="rl-dashboard-container h-full p-6 overflow-auto flex items-center justify-center">
        <Loader type="dots" message="Loading dashboard..." />
      </div>
    );
  }

  const weeklyChartData = processWeeklyData();
  const pieChartData = processTutorialStatusData();

  const statCards = [
    {
      title: 'Tutorials Generated',
      value: stats?.tutorials_generated || 0,
      icon: BookOpen,
      index: 0,
    },
    {
      title: 'Learning Hours',
      value: stats?.learning_hours || 0,
      suffix: 'hrs',
      icon: Clock,
      index: 1,
    },
    {
      title: 'Current Streak',
      value: stats?.current_streak || 0,
      suffix: 'days',
      icon: Flame,
      index: 2,
    },
    {
      title: 'Completed Tutorials',
      value: stats?.completed_tutorials || 0,
      icon: CheckCircle,
      index: 3,
    },
    {
      title: 'Total Hours This Week',
      value: stats?.total_hours_this_week || 0,
      suffix: 'hrs',
      icon: Calendar,
      index: 4,
    },
  ];

  return (
    <div className="rl-dashboard-container !max-w-[calc(100vw-220px)] !h-[calc(100vh-90px)] overflow-auto  h-full p-6 overflow-auto bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Header */}
      <div className="mb-8">
        <Title
          level={2}
          className="!mb-2 !text-3xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
        >
          Your Learning Journey
        </Title>
        <Text className="text-gray-600 text-lg">
          Track your progress and achievements
        </Text>
      </div>

      {/* Stats Cards */}
      <Row gutter={[16, 16]} className="mb-8">
        {statCards.map(card => (
          <Col xs={24} sm={12} lg={8} xl={8} key={card.title}>
            <StatCard
              title={card.title}
              value={card.value}
              suffix={card.suffix}
              icon={card.icon}
              color={STAT_CARD_COLORS[card.index % STAT_CARD_COLORS.length]}
              index={card.index}
            />
          </Col>
        ))}
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} className="mb-8">
        {/* Weekly Activity Chart */}
        <Col xs={24} lg={16}>
          <Card
            className="h-full border-0 shadow-lg"
            style={{ borderRadius: '16px' }}
            title={
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-600" />
                <span className="font-semibold">Weekly Activity</span>
              </div>
            }
          >
            {weeklyChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weeklyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="day" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar
                    dataKey="value"
                    fill="url(#colorGradient)"
                    radius={[8, 8, 0, 0]}
                  >
                    {weeklyChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          STAT_CARD_COLORS[index % STAT_CARD_COLORS.length].icon
                        }
                      />
                    ))}
                  </Bar>
                  <defs>
                    <linearGradient
                      id="colorGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="0%" stopColor="#667eea" stopOpacity={1} />
                      <stop offset="100%" stopColor="#764ba2" stopOpacity={1} />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty
                description="No activity data available"
                className="py-12"
              />
            )}
          </Card>
        </Col>

        {/* Tutorial Status Pie Chart */}
        <Col xs={24} lg={8}>
          <Card
            className="h-full border-0 shadow-lg"
            style={{ borderRadius: '16px' }}
            title={
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                <span className="font-semibold">Tutorial Status</span>
              </div>
            }
          >
            {pieChartData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PIE_COLORS[index % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty
                description="No tutorial data available"
                className="py-12"
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* Recent Activity */}
      <Card
        className="border-0 shadow-lg"
        style={{ borderRadius: '16px' }}
        title={
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-pink-600" />
            <span className="font-semibold">Repo Generation Activity</span>
          </div>
        }
      >
        {recentActivity?.activities && recentActivity.activities.length > 0 ? (
          <div className="space-y-4">
            {recentActivity.activities.map(activity => (
              <div
                key={activity.repo_id}
                className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-white to-slate-50 border border-slate-200 hover:shadow-md transition-all duration-300"
              >
                <div className="flex items-center gap-4 flex-1">
                  <div className="flex-shrink-0">
                    {getStatusIcon(activity.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Text strong className="text-base">
                        {activity.repo_name}
                      </Text>
                      <Tag
                        color={getStatusColor(activity.status)}
                        className="m-0"
                      >
                        {activity.status}
                      </Tag>
                    </div>
                    <Text type="secondary" className="text-sm block truncate">
                      {activity.repo_url}
                    </Text>
                    {activity.status === 'FAILED' && activity.error_message && (
                      <Text type="danger" className="text-xs block mt-1">
                        {activity.error_message}
                      </Text>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4 flex-shrink-0">
                  {[
                    'PROCESSING',
                    'GENERATING',
                    'ANALYZING',
                    'CLONING',
                  ].includes(activity.status) && (
                    <Progress
                      percent={activity.generation_progress || 0}
                      size="small"
                      strokeColor={{
                        '0%': '#667eea',
                        '100%': '#764ba2',
                      }}
                      style={{ width: 120 }}
                    />
                  )}
                  <Text type="secondary" className="text-xs">
                    {new Date(activity.created_at).toLocaleDateString()}
                  </Text>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty description="No recent activity" className="py-12" />
        )}
      </Card>
    </div>
  );
};

export default memo(Dashboard);
