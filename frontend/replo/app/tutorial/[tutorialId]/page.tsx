'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import TutorialPlayer from '@/components/tutorial/TutorialPlayer';

export default function TutorialPage() {
  const params = useParams();
  const tutorialId = params.tutorialId as string;

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 bg-gray-100 border-b flex items-center">
        <Link href="/dashboard" className="text-blue-600 hover:underline mr-4">
          &larr; Back to Dashboard
        </Link>
      </div>
      
      <div className="flex-grow overflow-hidden">
        <TutorialPlayer tutorialId={tutorialId} />
      </div>
    </div>
  );
}