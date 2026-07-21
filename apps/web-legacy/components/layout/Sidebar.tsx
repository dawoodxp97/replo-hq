'use client';

import { usePathname, useRouter } from 'next/navigation';
import {
  BookOpen,
  Edit3,
  Folder,
  Home,
  Library,
  Settings,
  Sparkles,
  TrendingUp,
} from 'lucide-react';

type View =
  | 'dashboard'
  | 'tutorial'
  | 'progress'
  | 'authoring'
  | 'library'
  | 'settings';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'my-tutorials', label: 'My Tutorials', icon: Library },
  { id: 'progress', label: 'Progress', icon: TrendingUp },
  { id: 'authoring', label: 'Author', icon: Edit3 },
  { id: 'repo', label: 'Repositories', icon: Folder },
];
export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname() ?? '/';
  const currentView = pathname.split('/')[1] as View;
  return (
    <aside className="w-55 bg-[var(--background-soft)] backdrop-blur-xl border-r border-gray-200/50 flex flex-col shadow-xl">
      <div className="flex-1 px-4 space-y-1 pt-4">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <div
              key={item.id}
              onClick={() => router.push(`/${item.id}`)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group mt-2 cursor-pointer ${
                isActive
                  ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-md shadow-blue-500/10'
                  : 'text-gray-600 hover:bg-gray-50 hover:shadow-sm'
              }`}
            >
              <Icon
                className={`w-5 h-5 transition-transform ${
                  isActive ? 'scale-110' : 'group-hover:scale-110'
                }`}
              />
              <span className="font-medium">{item.label}</span>
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full animate-pulse"></div>
              )}
            </div>
          );
        })}
      </div>

      <div className="p-4 border-t border-gray-200/50">
        <button
          onClick={() => router.push('/settings')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group cursor-pointer ${
            currentView === 'settings'
              ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 shadow-md shadow-blue-500/10'
              : 'text-gray-600 hover:bg-gray-50 hover:shadow-sm'
          }`}
        >
          <Settings
            className={`w-5 h-5 transition-transform ${
              currentView === 'settings'
                ? 'rotate-90 scale-110'
                : 'group-hover:rotate-90 group-hover:scale-110'
            }`}
          />
          <span className="font-medium">Settings</span>
        </button>
      </div>
    </aside>
  );
}
