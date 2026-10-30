import { useCallback, useEffect, useState } from 'react';
import { explore } from '@/services/tutorials';
import type { ExploreTutorialItem, Page_ExploreTutorialItem_ } from '@replo/api-client';
import { EmptyState, ErrorState, Loading } from '@/components/states';
import { TutorialCard } from '@/components/TutorialCard';

const LANGUAGES = ['', 'python', 'typescript', 'javascript', 'go', 'rust', 'java'];

export function ExplorePage() {
  const [language, setLanguage] = useState('');
  const [page, setPage] = useState<Page_ExploreTutorialItem_ | null>(null);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(() => {
    setError(null);
    setPage(null);
    explore({ language: language || null, limit: 50 })
      .then(setPage)
      .catch(setError);
  }, [language]);

  useEffect(load, [load]);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!page) return <Loading />;

  const items: ExploreTutorialItem[] = page.items;
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Explore public tutorials</h1>
        <select className="rounded-md border px-3 py-1.5 text-sm" value={language} onChange={(e) => setLanguage(e.target.value)}>
          {LANGUAGES.map((l) => (
            <option key={l} value={l}>{l === '' ? 'All languages' : l}</option>
          ))}
        </select>
      </div>
      {items.length === 0 ? (
        <EmptyState title="Nothing published here yet" hint={language ? `No public ${language} tutorials yet.` : 'No public tutorials yet.'} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((t) => (
            <TutorialCard key={t.tutorial_id} tutorial={{ ...t, external: t.slug ? `/site/t/${t.slug}` : undefined }} />
          ))}
        </div>
      )}
    </div>
  );
}
