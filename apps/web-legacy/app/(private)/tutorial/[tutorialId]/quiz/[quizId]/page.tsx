import React from 'react';
import { notFound } from 'next/navigation';
import { z } from 'zod';
const ParamsSchema = z.object({ tutorialId: z.string().nonempty(), quizId: z.string().nonempty() });

export default function TutorialQuizPage({ params }: { params: { tutorialId?: string; quizId?: string } }) {
  const parse = ParamsSchema.safeParse(params);
  if (!parse.success) {
    notFound();
  }

  const { tutorialId, quizId } = parse.data;
  return (
    <div className="p-6">
      <h1 className="text-xl font-bold">Quiz</h1>
      <p className="text-sm text-gray-600">Tutorial: {tutorialId}</p>
      <p className="text-sm text-gray-600">Quiz: {quizId}</p>
    </div>
  );
}