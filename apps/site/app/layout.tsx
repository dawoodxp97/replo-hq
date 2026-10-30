import type { Metadata } from 'next';
import './globals.css';
import Nav from '@/components/landing/Nav';
import Footer from '@/components/landing/Footer';

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3100'),
  title: { default: 'Replo — turn any repo into a tutorial', template: '%s | Replo' },
  alternates: { canonical: '/' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        {children}
        <Footer />
      </body>
    </html>
  );
}
