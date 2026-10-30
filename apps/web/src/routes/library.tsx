import { useCallback, useEffect, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { Button } from '@replo/ui';
import { library, remove as removeTutorial, setVisibility } from '@/services/tutorials';
import type { Page_TutorialListItem_, TutorialListItem } from '@replo/api-client';
import { EmptyState, ErrorState, Loading } from '@/components/states';
import { TutorialCard } from '@/components/TutorialCard';

export function LibraryPage() {
  const [page, setPage] = useState<Page_TutorialListItem_ | null>(null);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(() => {
    setError(null);
    setPage(null);
    library({ limit: 50 })
      .then(setPage)
      .catch(setError);
  }, []);

  useEffect(load, [load]);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!page) return <Loading />;

  const items: TutorialListItem[] = page.items;
  if (items.length === 0) {
    return (
      <EmptyState
        title="No tutorials yet"
        hint="Point Replo at a repository and it will build a walkthrough for you."
        action={<Link to="/generate" className="inline-flex h-10 items-center rounded-md bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700">Generate your first tutorial</Link>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Library</h1>
        <Link to="/generate" className="inline-flex h-10 items-center rounded-md bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700">New tutorial</Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((t) => (
          <div key={t.tutorial_id} className="space-y-2">
            <TutorialCard tutorial={t} />
            <div className="flex gap-3 text-xs text-neutral-500">
              <button
                className="underline"
                onClick={() => {
                  void setVisibility(t.tutorial_id, t.visibility === 'public' ? 'private' : 'public').then(load);
                }}
              >
                Make {t.visibility === 'public' ? 'private' : 'public'}
              </button>
              <button
                className="underline hover:text-red-600"
                onClick={() => {
                  void removeTutorial(t.tutorial_id).then(load);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
      {page.has_more ? (
        <Button variant="secondary" onClick={() => library({ limit: 50, offset: page.offset + page.limit }).then(setPage)}>
          Load more
        </Button>
      ) : null}
    </div>
  );
}
