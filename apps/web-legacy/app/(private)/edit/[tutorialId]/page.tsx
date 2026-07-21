import React from 'react';
import { notFound } from 'next/navigation';
import { z } from 'zod';
import TutorialEditor from '@/components/author/TutorialEditor';

const ParamsSchema = z.object({ tutorialId: z.string().nonempty() });

export default function EditTutorialPage({ params }: { params: { tutorialId?: string } }) {
  const parse = ParamsSchema.safeParse(params);
  if (!parse.success) {
    notFound();
  }

  const { tutorialId } = parse.data;
  return <TutorialEditor tutorialId={tutorialId} />;
}