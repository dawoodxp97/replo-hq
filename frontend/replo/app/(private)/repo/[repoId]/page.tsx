import React from 'react';
import { notFound } from 'next/navigation';
import { z } from 'zod';

const ParamsSchema = z.object({ repoId: z.string().nonempty() });

export default function RepoPage({ params }: { params: { repoId?: string } }) {
  const parse = ParamsSchema.safeParse(params);
  if (!parse.success) {
    notFound();
  }

  const { repoId } = parse.data;
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Repo: {repoId}</h1>
      <p className="text-gray-600">Repository details go here.</p>
    </div>
  );
}