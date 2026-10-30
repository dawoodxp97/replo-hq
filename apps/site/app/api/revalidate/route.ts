import { revalidateTag } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';
import { TAGS } from '@/lib/api';

/**
 * On-demand revalidation. The API calls this after a tutorial's visibility
 * or content changes; the shared secret keeps it unguessable.
 */
export async function POST(request: NextRequest) {
  const secret = request.nextUrl.searchParams.get('secret');
  if (!process.env.REVALIDATE_SECRET || secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 });
  }
  const tag = request.nextUrl.searchParams.get('tag');
  const slug = request.nextUrl.searchParams.get('slug');
  if (tag === TAGS.explore) revalidateTag(TAGS.explore, 'max');
  else if (slug) revalidateTag(TAGS.tutorial(slug), 'max');
  else return NextResponse.json({ error: 'tag or slug required' }, { status: 400 });
  return NextResponse.json({ revalidated: true });
}
