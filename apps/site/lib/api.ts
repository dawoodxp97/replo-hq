/**
 * Server-side data access for the public site. One place owns base URL,
 * caching/revalidation tags and error mapping — pages stay declarative.
 */
import 'server-only';
import type { ExploreTutorialItem, Page_ExploreTutorialItem_, TutorialResponse } from '@replo/api-client';

export const API_URL = process.env.REPLO_API_URL ?? 'http://localhost:8000';

export const TAGS = {
  tutorial: (slug: string) => `tutorial:${slug}`,
  explore: 'explore',
} as const;

export class SiteApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'SiteApiError';
    this.status = status;
  }
}

async function get<T>(path: string, tag: string, revalidate = 300): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { next: { tags: [tag], revalidate } });
  if (!response.ok) {
    throw new SiteApiError(response.status, response.status === 404 ? 'Not found' : 'Upstream API error');
  }
  return (await response.json()) as T;
}

export const getTutorialBySlug = (slug: string) =>
  get<TutorialResponse>(`/api/tutorial/slug/${encodeURIComponent(slug)}`, TAGS.tutorial(slug));

export const getExplore = (params: { language?: string | null; limit?: number; offset?: number }) => {
  const search = new URLSearchParams();
  if (params.language) search.set('language', params.language);
  if (params.limit != null) search.set('limit', String(params.limit));
  if (params.offset != null) search.set('offset', String(params.offset));
  const qs = search.toString();
  return get<Page_ExploreTutorialItem_>(`/api/tutorial/explore${qs ? `?${qs}` : ''}`, TAGS.explore);
};

export type { ExploreTutorialItem, TutorialResponse };
