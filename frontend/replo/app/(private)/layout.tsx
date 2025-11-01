import React from 'react';
import { Header } from '@/components/core/Header';
import { Sidebar } from '@/components/core/Sidebar';

export default function PrivateLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-private-root flex flex-col h-screen bg-[var(--background-soft)]">
      <Header />
      <div className="private-grid flex flex-1">
        <Sidebar />
        <main className="flex-1 shadow-md bg-[#FBFCFF]">{children}</main>
      </div>
    </div>
  );
}