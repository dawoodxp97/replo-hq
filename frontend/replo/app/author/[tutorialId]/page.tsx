'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import TutorialEditor from '@/components/author/TutorialEditor';

export default function AuthorPage() {
  const params = useParams();
  const tutorialId = params.tutorialId as string;

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 bg-gray-100 border-b flex items-center">
        <Link href="/dashboard" className="text-blue-600 hover:underline mr-4">
          &larr; Back to Dashboard
        </Link>
        <h1 className="text-xl font-semibold">Tutorial Editor</h1>
      </div>
      
      <div className="flex-grow overflow-hidden">
        <TutorialEditor tutorialId={tutorialId} />
      </div>
    </div>
  );
}