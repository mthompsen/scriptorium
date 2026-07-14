import type { Metadata } from 'next';
import Link from 'next/link';
import type { ReactNode } from 'react';

import './globals.css';

export const metadata: Metadata = {
  title: 'Scriptorium',
  description: 'Enterprise knowledge intelligence platform',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-slate-900 focus:px-4 focus:py-2 focus:text-white"
        >
          Skip to main content
        </a>
        <header className="border-b border-slate-200 bg-white">
          <nav
            aria-label="Main"
            className="mx-auto flex max-w-4xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3"
          >
            <Link href="/" className="font-semibold tracking-tight">
              Scriptorium
            </Link>
            <Link href="/chat" className="text-sm text-slate-600 hover:text-slate-900">
              Chat
            </Link>
            <Link href="/library" className="text-sm text-slate-600 hover:text-slate-900">
              Library
            </Link>
            <Link href="/graph" className="text-sm text-slate-600 hover:text-slate-900">
              Graph
            </Link>
            <Link href="/admin" className="text-sm text-slate-600 hover:text-slate-900">
              Admin
            </Link>
            <Link href="/login" className="ml-auto text-sm text-slate-600 hover:text-slate-900">
              Sign in
            </Link>
          </nav>
        </header>
        <main id="main" className="mx-auto max-w-4xl px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
