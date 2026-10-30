import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from '@tanstack/react-router';
import { MarkdownRenderer, Button } from '@replo/ui';
import { get } from '@/services/tutorials';
import { completeModule, submitQuiz, uncompleteModule } from '@/services/progress';
import type {
  app__schemas__tutorial__ModuleResponse,
  app__schemas__tutorial__QuizResponse,
  TutorialResponse,
} from '@replo/api-client';
import { ErrorState, Loading } from '@/components/states';

function QuizBlock({ quiz, moduleId }: { quiz: app__schemas__tutorial__QuizResponse; moduleId: string }) {
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState<{ is_correct: boolean; correct_answer?: string | null } | null>(null);
  const [error, setError] = useState<unknown>(null);

  const submit = async () => {
    if (!selected) return;
    setError(null);
    try {
      setResult(await submitQuiz({ quiz_id: quiz.quiz_id, submitted_answer: selected }));
    } catch (err) {
      setError(err);
    }
  };

  return (
    <div className="mt-6 rounded-lg border border-neutral-200 p-4">
      <p className="font-medium">{quiz.question_text}</p>
      {error ? <p className="mt-2 text-sm text-red-600">{error instanceof Error ? error.message : 'Quiz failed'}</p> : null}
      <div className="mt-3 space-y-2">
        {(quiz.options ?? []).map((o, i) => (
          <label key={o.id ?? i} className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name={`quiz-${moduleId}`}
              checked={selected === (o.id ?? o.text)}
              disabled={Boolean(result)}
              onChange={() => setSelected(o.id ?? o.text)}
            />
            <span>{o.text}</span>
          </label>
        ))}
      </div>
      {result ? (
        <p className={`mt-3 text-sm font-medium ${result.is_correct ? 'text-green-700' : 'text-red-700'}`}>
          {result.is_correct ? 'Correct!' : `Not quite — correct answer: ${result.correct_answer ?? ''}`}
        </p>
      ) : (
        <Button size="sm" className="mt-3" disabled={!selected} onClick={() => void submit()}>Check answer</Button>
      )}
    </div>
  );
}

export function TutorialPlayerPage() {
  const { tutorialId = '' } = useParams({ strict: false }) as { tutorialId?: string };
  const [tutorial, setTutorial] = useState<TutorialResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  const load = useCallback(() => {
    setError(null);
    setTutorial(null);
    void get(tutorialId)
      .then(setTutorial)
      .catch(setError);
  }, [tutorialId]);

  useEffect(load, [load]);

  const mods: app__schemas__tutorial__ModuleResponse[] = useMemo(
    () => [...(tutorial?.modules ?? [])].sort((a, b) => a.order_index - b.order_index),
    [tutorial],
  );
  const active = useMemo(() => mods[activeIndex], [mods, activeIndex]);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!tutorial) return <Loading />;

  return (
    <div className="grid gap-8 md:grid-cols-[220px_1fr]">
      <aside className="space-y-1">
        <h1 className="mb-3 text-lg font-semibold">{tutorial.title}</h1>
        {mods.map((m, i) => (
          <button
            key={m.module_id}
            className={`block w-full rounded px-2 py-1.5 text-left text-sm ${i === activeIndex ? 'bg-neutral-100 font-medium' : 'hover:bg-neutral-50'} ${completed.has(m.module_id) ? 'text-green-700' : ''}`}
            onClick={() => setActiveIndex(i)}
          >
            {i + 1}. {m.title}
          </button>
        ))}
      </aside>
      <article className="min-w-0">
        {active ? (
          <>
            <h2 className="text-xl font-semibold">{active.title}</h2>
            <MarkdownRenderer content={active.content_markdown} />
            {active.quiz ? <QuizBlock quiz={active.quiz} moduleId={active.module_id} /> : null}
            <div className="mt-8 flex justify-between">
              <Button variant="secondary" disabled={activeIndex === 0} onClick={() => setActiveIndex((i) => i - 1)}>Previous</Button>
              {completed.has(active.module_id) ? (
                <Button variant="secondary" onClick={() => void uncompleteModule(active.module_id).then(() => setCompleted((s) => { const n = new Set(s); n.delete(active.module_id); return n; }))}>
                  Mark incomplete
                </Button>
              ) : (
                <Button onClick={() => void completeModule(active.module_id).then(() => setCompleted((s) => new Set(s).add(active.module_id)))}>
                  Mark complete
                </Button>
              )}
              {activeIndex < mods.length - 1 ? (
                <Button onClick={() => setActiveIndex((i) => i + 1)}>Next</Button>
              ) : null}
            </div>
          </>
        ) : (
          <Loading label="Loading module…" />
        )}
      </article>
    </div>
  );
}
