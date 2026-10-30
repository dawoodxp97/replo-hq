import type { MetadataRoute } from 'next';
import { getExplore } from '@/lib/api';

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3100';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [
    { url: `${BASE}/`, changeFrequency: 'weekly', priority: 1 },
    { url: `${BASE}/explore`, changeFrequency: 'daily', priority: 0.8 },
  ];
  try {
    const page = await getExplore({ limit: 500 });
    for (const item of page.items) {
      if (item.slug) entries.push({ url: `${BASE}/t/${item.slug}`, changeFrequency: 'weekly', priority: 0.6 });
    }
  } catch {
    // The API being down must not take the sitemap (and thus the build) down.
  }
  return entries;
}
