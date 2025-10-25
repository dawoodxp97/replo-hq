'use client';

import RepoSubmitForm from '@/components/dashboard/RepoSubmitForm';
import RepoList from '@/components/dashboard/RepoList';

export default function DashboardPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">ReploAI Dashboard</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column - Submit form */}
        <div className="lg:col-span-1">
          <RepoSubmitForm />
        </div>
        
        {/* Right column - Repository list */}
        <div className="lg:col-span-2">
          <RepoList />
        </div>
      </div>
    </div>
  );
}