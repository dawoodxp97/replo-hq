'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Avatar, Badge, Dropdown } from 'antd';
import { Bell, Sparkles, User } from 'lucide-react';

import {
  aiGradientBackground,
  borderGradientDefault,
  borderGradientFocus,
  boxShadows,
} from '@/constants/gradientColors';
import { useGlobalStore } from '@/store/useGlobalStore';

import Notification from '../common/notification/Notification';
import Search from '../features/search/Search';

export default function Navbar() {
  const { user, logout } = useGlobalStore();
  const router = useRouter();
  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      label: 'Profile',
      onClick: () => router.push('/settings/#profile'),
    },
    {
      key: 'logout',
      label: 'Logout',
      danger: true,
      onClick: handleLogout,
    },
  ];

  return (
    <nav
      className={`flex items-center justify-between !p-4 ${'bg-[var(--background-soft)]'} shadow-sm border-b-[#ececec] border-b border-solid`}
    >
      <div className="flex items-center justify-center px-4">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 group w-full"
        >
          <div className="relative">
            <div className="w-11 h-11 bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-xl group-hover:shadow-indigo-500/30 transition-all duration-300 ai-pulse">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-br from-yellow-300 to-orange-400 rounded-full animate-pulse shadow-md"></div>
          </div>
          <div>
            <span className="text-slate-900 font-bold text-lg bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Replo AI
            </span>
            <p className=" !mb-0 text-xs text-slate-500 flex items-center gap-1 mt-0.5">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
              AI-Powered
            </p>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <>
          <Search />
          <Notification />
          <div className="profile-container">
            <Dropdown
              menu={{ items: userMenuItems }}
              trigger={['click']}
              placement="bottomRight"
            >
              <div className="profile-button-wrapper">
                <button className="profile-button flex items-center gap-2 lg:gap-3 px-3 lg:px-4 py-2 rounded-xl bg-white transition-all duration-200 group flex-shrink-0">
                  <Avatar
                    size={32}
                    className="bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 shadow-md group-hover:shadow-lg transition-all flex-shrink-0"
                    icon={<User className="w-4 h-4 text-white" />}
                  />
                  <span className="max-w-[100px] text-ellipsis overflow-hidden whitespace-nowrap text-sm font-medium text-slate-700 hidden sm:inline">
                    {user?.firstName || user?.email || 'User'}{' '}
                    {user?.lastName || ''}
                  </span>
                </button>
              </div>
            </Dropdown>
          </div>
        </>
      </div>
      <style jsx>{`
        /* Profile button gradient border wrapper */
        .profile-container .profile-button-wrapper {
          position: relative;
          border-radius: 0.75rem;
          padding: 1px;
          background: ${borderGradientDefault};
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          display: inline-block;
        }

        /* Profile button - white background by default */
        .profile-container .profile-button {
          background: white !important;
        }

        /* Profile button focus state */
        .profile-container .profile-button:focus,
        .profile-container .profile-button:focus-visible {
          outline: none;
          color: white !important;
          background: ${aiGradientBackground} !important;
        }

        /* Text color white on focus */
        .profile-container .profile-button:focus span,
        .profile-container .profile-button:focus-visible span {
          color: white !important;
        }

        /* Enhanced border on focus - keep same width */
        .profile-container .profile-button-wrapper:has(.profile-button:focus),
        .profile-container
          .profile-button-wrapper:has(.profile-button:focus-visible) {
          background: ${borderGradientFocus} !important;
          box-shadow: ${boxShadows.focus} !important;
        }

        /* Shiny white shadow on avatar icon on focus */
        .profile-container .profile-button:focus .ant-avatar,
        .profile-container .profile-button:focus-visible .ant-avatar {
          box-shadow: 0 0 10px rgba(255, 255, 255, 0.8),
            0 0 20px rgba(255, 255, 255, 0.5), 0 0 30px rgba(255, 255, 255, 0.3) !important;
        }
      `}</style>
    </nav>
  );
}
