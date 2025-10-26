"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

// Define the expected progress payload from the API
interface UserProgress {
  modules_completed: Array<{ title?: string }>;
  last_updated: string | null;
}

export default function ProgressTracker() {
  const { data, error, isLoading } = useQuery<UserProgress>({
    queryKey: ["progress"],
    queryFn: async () => {
      const response: any = await apiClient.get(API_ENDPOINTS.PROGRESS_GET);
      // Support both AxiosResponse and plain data returns
      return (response?.data ?? response) as UserProgress;
    },
  });

  if (isLoading) {
    return <div className="p-6">Loading progress...</div>;
  }
  if (error) {
    return <div className="p-6 text-red-600">Failed to load progress.</div>;
  }

  const progress: UserProgress = data ?? { modules_completed: [], last_updated: null };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Your Progress</h1>
      <ul className="space-y-2">
        {progress.modules_completed?.length ? (
          progress.modules_completed.map((m: any, i: number) => (
            <li key={i} className="p-3 border rounded bg-white">
              <div className="font-medium">{m.title || `Module ${i + 1}`}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </li>
          ))
        ) : (
          <li className="p-3 border rounded bg-white">No progress yet.</li>
        )}
      </ul>
      {progress.last_updated && (
        <div className="mt-4 text-sm text-gray-500">Last updated: {progress.last_updated}</div>
      )}
    </div>
  );
}