import { describe, expect, it, vi } from 'vitest';

// lib/api imports 'server-only' — stub it for node tests.
vi.mock('server-only', () => ({}));

describe('site data layer', () => {
  it('maps a 404 from the API to SiteApiError with status 404', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{"detail":"not found"}', { status: 404 })));
    const { getTutorialBySlug, SiteApiError } = await import('@/lib/api');
    await expect(getTutorialBySlug('nope')).rejects.toBeInstanceOf(SiteApiError);
    vi.unstubAllGlobals();
  });

  it('builds the explore query with a language filter', async () => {
    let called = '';
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      called = String(input);
      return new Response(JSON.stringify({ items: [], total: 0, limit: 50, offset: 0, has_more: false }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }));
    const { getExplore } = await import('@/lib/api');
    await getExplore({ language: 'python', limit: 50 });
    expect(called).toContain('/api/tutorial/explore?language=python&limit=50');
    vi.unstubAllGlobals();
  });
});
