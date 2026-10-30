import type { Metadata } from 'next';
import Link from 'next/link';
import { getExplore } from '@/lib/api';
import type { ExploreTutorialItem } from '@replo/api-client';

export const revalidate = 300;

export const metadata: Metadata = {
  title: 'Explore public tutorials',
  alternates: { canonical: '/explore' },
};

const LANGUAGES = ['', 'python', 'typescript', 'javascript', 'go', 'rust', 'java'];

type Props = { searchParams: Promise<{ language?: string }> };

export default async function ExplorePage({ searchParams }: Props) {
  const { language = '' } = await searchParams;
  let page: Awaited<ReturnType<typeof getExplore>> | null = null;
  try {
    page = await getExplore({ language: language || null, limit: 50 });
  } catch {
    page = null;
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-bold">Explore public tutorials</h1>
        <form className="flex gap-2" action="/explore">
          <select name="language" defaultValue={language} className="rounded-md border px-3 py-1.5 text-sm">
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>{l === '' ? 'All languages' : l}</option>
            ))}
          </select>
          <button className="rounded-md border px-3 py-1.5 text-sm">Filter</button>
        </form>
      </div>
      {!page || page.items.length === 0 ? (
        <p className="mt-10 text-neutral-500">Nothing published here yet.</p>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {page.items.map((t: ExploreTutorialItem) => (
            <Link
              key={t.tutorial_id}
              href={t.slug ? `/t/${t.slug}` : '/explore'}
              className="block rounded-lg border border-neutral-200 p-4 transition hover:border-neutral-400"
            >
              <div className="flex items-center justify-between">
                <h2 className="font-medium">{t.title}</h2>
                <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs uppercase">{t.level}</span>
              </div>
              {t.overview ? <p className="mt-2 line-clamp-2 text-sm text-neutral-600">{t.overview}</p> : null}
              <div className="mt-3 flex items-center justify-between text-xs text-neutral-500">
                <span>{t.repo_name ?? ''}</span>
                {t.language ? <span>{t.language}</span> : null}
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
