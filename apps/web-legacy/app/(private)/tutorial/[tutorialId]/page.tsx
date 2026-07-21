'use client';

import React from 'react';
import { notFound, useParams } from 'next/navigation';
import { z } from 'zod';
import TutorialPlayer from '@/components/features/tutorial/TutorialPlayer';

const ParamsSchema = z.object({ tutorialId: z.string().min(1) });

export default function TutorialPlaybackPage() {
  const params = useParams();
  
  const parse = ParamsSchema.safeParse(params);
  if (!parse.success) {
    notFound();
  }

  const { tutorialId } = parse.data;
  return <TutorialPlayer tutorialId={tutorialId} />;
}