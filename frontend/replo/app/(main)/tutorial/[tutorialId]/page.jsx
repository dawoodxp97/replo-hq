// ./frontend/src/app/(main)/tutorial/[tutorialId]/page.jsx
"use client";

import { useEffect, useState } from "react";
// Import your new components
// import SplitScreenViewer from "@/components/tutorial/SplitScreenViewer";

// This component receives 'params' from the URL
export default function TutorialPage({ params }) {
  const { tutorialId } = params;
  const [tutorial, setTutorial] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (tutorialId) {
      // Fetch the specific tutorial data from your FastAPI backend
      fetch(`http://localhost:8000/api/v1/tutorial/${tutorialId}`)
        .then((res) => res.json())
        .then((data) => {
          setTutorial(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Failed to fetch tutorial:", err);
          setLoading(false);
        });
    }
  }, [tutorialId]);

  if (loading) {
    return <div className="p-8">Loading tutorial...</div>;
  }

  if (!tutorial) {
    return <div className="p-8">Tutorial not found.</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold p-4">
        Tutorial: {tutorial.title} (ID: {tutorialId})
      </h1>

      {/* This is where you'll build your main UI:
        <SplitScreenViewer
          explanation={tutorial.modules[0].explanation}
          code={tutorial.modules[0].interactiveExample}
          diagram={tutorial.diagramData}
        />
      */}

      <pre className="bg-gray-100 p-4 rounded-md">
        {JSON.stringify(tutorial, null, 2)}
      </pre>
    </div>
  );
}