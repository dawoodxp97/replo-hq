"use client";

import { useQuery } from "@tanstack/react-query";
// 1. Import your new service
import { getTutorialById } from "@/services/tutorialService"; 

export default function TutorialPage({ params }) {
  const { tutorialId } = params;

  const { data: tutorial, error, isLoading } = useQuery({
    queryKey: ["tutorial", tutorialId],
    // 2. The queryFn is now just a call to your service!
    // It's clean and readable. The service returns the promise.
    queryFn: () => getTutorialById(tutorialId),
  });

  if (isLoading) return <div className="p-8">Loading tutorial...</div>;
  if (error) return <div className="p-8">Error: {error.message}</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold p-4">
        Tutorial: {tutorial.title}
      </h1>
      <pre className="bg-gray-100 p-4 rounded-md">
        {JSON.stringify(tutorial, null, 2)}
      </pre>
    </div>
  );
}