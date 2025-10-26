import React from 'react';
import { notFound } from 'next/navigation';
import { z } from 'zod';
import TutorialPlayer from '@/components/features/tutorial/TutorialPlayer';

const ParamsSchema = z.object({ tutorialId: z.string().nonempty() });

export default function TutorialPlaybackPage({ params }: { params: { tutorialId?: string } }) {
  const parse = ParamsSchema.safeParse(params);
  if (!parse.success) {
    notFound();
  }

  const { tutorialId } = parse.data;
  return <TutorialPlayer tutorialId={tutorialId} />;
}