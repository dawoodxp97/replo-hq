import { useGlobalStore } from '@/store/useGlobalStore';
import { Button, Card, Typography } from 'antd';
import router from 'next/router';
import { memo } from 'react';

const Dashboard = () => {
  const { user } = useGlobalStore();
  console.log(user);
  return (
    <div className="rl-dashboard-container h-full p-6 overflow-auto">
      <div className="welcome-back-info">
        <Typography.Title level={3} className="text-2xl font-bold !mb-0">
          Welcome back, {user?.firstName || 'User'} {user?.lastName || ''}
        </Typography.Title>
        <Typography.Text className="!text-gray-600">
          Transform any GitHub repository into interactive tutorials with AI.
        </Typography.Text>
      </div>
      <div className="generate-tutorial-info-card"></div>
    </div>
  );
};

export default memo(Dashboard);
