import React from 'react';
import { Header } from '@/components/core/Header';
import { Sidebar } from '@/components/core/Sidebar';

export default function PrivateLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-private-root">
      <Header />
      <div className="private-grid flex">
        <aside className="w-64 border-r">
          <Sidebar />
        </aside>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}