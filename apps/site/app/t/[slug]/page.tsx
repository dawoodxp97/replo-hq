import type { Metadata } from 'next';
import Link from 'next/link';
import { MarkdownRenderer } from '@replo/ui';
import { getTutorialBySlug, SiteApiError } from '@/lib/api';

// Public tutorials are readable without authentication (decision D8); the
// ISR window plus the on-demand revalidate route keep them fresh without a
// request-time API dependency.
export const revalidate = 300;

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const tutorial = await getTutorialBySlug(slug);
    return {
      title: tutorial.title,
      description: tutorial.overview ?? undefined,
      alternates: { canonical: `/t/${slug}` },
      openGraph: { title: tutorial.title, description: tutorial.overview ?? undefined, type: 'article' },
    };
  } catch {
    return { title: 'Tutorial not found' };
  }
}

export default async function PublicTutorialPage({ params }: Props) {
  const { slug } = await params;
  let tutorial;
  try {
    tutorial = await getTutorialBySlug(slug);
  } catch (error) {
    if (error instanceof SiteApiError && error.status === 404) {
      return (
        <main className="mx-auto max-w-2xl px-6 py-20 text-center">
          <h1 className="text-2xl font-semibold">Tutorial not found</h1>
          <p className="mt-2 text-neutral-500">It may be private or removed.</p>
          <Link href="/explore" className="mt-6 inline-block underline">Browse public tutorials</Link>
        </main>
      );
    }
    throw error;
  }

  const modules = [...tutorial.modules].sort((a, b) => a.order_index - b.order_index);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <p className="text-sm text-neutral-500">{tutorial.repo_name ?? ''}</p>
      <h1 className="text-3xl font-bold">{tutorial.title}</h1>
      {tutorial.overview ? <p className="mt-3 text-neutral-600">{tutorial.overview}</p> : null}
      <article className="mt-10 space-y-12">
        {modules.map((m) => (
          <section key={m.module_id}>
            <h2 className="text-xl font-semibold">{m.title}</h2>
            <MarkdownRenderer content={m.content_markdown} />
            {/* D8: quizzes stay disabled on the public site — no login wall. */}
            {m.quiz ? (
              <div className="mt-4 rounded-lg border border-dashed border-neutral-300 p-4 text-sm text-neutral-500">
                Quiz available in the product after signing in.
              </div>
            ) : null}
          </section>
        ))}
      </article>
      <div className="mt-16 border-t pt-6">
        <a href={process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'} className="font-medium underline">
          Generate a tutorial for your repo →
        </a>
      </div>
    </main>
  );
}
