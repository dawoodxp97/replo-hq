import type { Metadata } from 'next';
import { Open_Sans, Source_Sans_3 } from 'next/font/google';
import 'antd/dist/reset.css';
import '../styles/globals.css';
import Providers from '@/providers/tanstack/reactQuery.provider';
import AntdStyledComponentsRegistry from '@/components/core/AntdStyledComponentsRegistry';

const openSans = Open_Sans({
  variable: '--font-open-sans',
  subsets: ['latin'],
});

const sourceSans = Source_Sans_3({
  variable: '--font-source-sans',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title:
    'Replo AI - Turn Any Codebase Into Interactive Tutorials Automatically',
  description:
    'Transform any GitHub repository into step-by-step interactive tutorials automatically. AI-powered code learning with interactive examples, diagrams, and quizzes.',
  keywords: [
    'AI tutorial generator',
    'code learning platform',
    'interactive coding tutorials',
    'GitHub repo analyzer',
    'developer education',
    'code tutorial generator',
    'learn to code',
    'AI-powered learning',
  ],
  authors: [{ name: 'Replo AI' }],
  creator: 'Replo AI',
  publisher: 'Replo AI',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL || 'https://reploai.com'
  ),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title:
      'Replo AI - Turn Any Codebase Into Interactive Tutorials Automatically',
    description:
      'Transform any GitHub repository into step-by-step interactive tutorials automatically. AI-powered code learning with interactive examples, diagrams, and quizzes.',
    url: '/',
    siteName: 'Replo AI',
    images: [
      {
        url: '/og-image.png', // TODO: Add actual OG image
        width: 1200,
        height: 630,
        alt: 'Replo AI - AI-Powered Code Tutorial Generator',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Replo AI - Turn Any Codebase Into Interactive Tutorials',
    description:
      'Transform any GitHub repository into step-by-step interactive tutorials automatically.',
    images: ['/og-image.png'], // TODO: Add actual Twitter card image
    creator: '@reploai', // TODO: Update with actual Twitter handle
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    // TODO: Add verification codes when available
    // google: 'your-google-verification-code',
    // yandex: 'your-yandex-verification-code',
    // yahoo: 'your-yahoo-verification-code',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${openSans.variable} ${sourceSans.variable} antialiased`}
      >
        <AntdStyledComponentsRegistry>
          <Providers>{children}</Providers>
        </AntdStyledComponentsRegistry>
      </body>
    </html>
  );
}
