import { ImageResponse } from 'next/og';
import { getTutorialBySlug } from '@/lib/api';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default async function OgImage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let title = 'Replo';
  let overview = 'Turn any repository into a tutorial.';
  try {
    const tutorial = await getTutorialBySlug(slug);
    title = tutorial.title;
    overview = tutorial.overview ?? overview;
  } catch {
    // A generic OG image is better than a failed render.
  }
  return new ImageResponse(
    (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', width: '100%', height: '100%', padding: 64, background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)', color: 'white' }}>
        <div style={{ fontSize: 28, opacity: 0.8 }}>Replo</div>
        <div style={{ fontSize: 56, fontWeight: 700, marginTop: 12, maxWidth: 900 }}>{title}</div>
        <div style={{ fontSize: 24, opacity: 0.9, marginTop: 16, maxWidth: 900 }}>{overview}</div>
      </div>
    ),
    size,
  );
}
