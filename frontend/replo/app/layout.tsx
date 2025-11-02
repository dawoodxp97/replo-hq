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
  title: 'Replo',
  description: 'Turn any github repos into interactive tutorials',
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
