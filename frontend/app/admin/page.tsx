'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { api, ApiError, Principal } from '@/lib/api';

const LEGACY_ADMIN_URL =
  process.env.NEXT_PUBLIC_LEGACY_ADMIN_URL ?? 'http://localhost:8080/legacy/admin/';

export default function AdminPage() {
  const router = useRouter();
  const [principal, setPrincipal] = useState<Principal | null>(null);

  useEffect(() => {
    api<Principal>('/auth/me')
      .then(setPrincipal)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) {
          router.replace('/login');
        }
      });
  }, [router]);

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Admin</h1>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-medium text-slate-600">Your session</h2>
        {principal ? (
          <dl className="mt-2 grid grid-cols-1 gap-x-8 gap-y-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">User</dt>
              <dd>{principal.email}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Roles</dt>
              <dd>{principal.roles.join(', ')}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-slate-500">Tenant</dt>
              <dd>
                <code className="text-xs">{principal.tenantId}</code>
              </dd>
            </div>
          </dl>
        ) : (
          <p className="mt-2 text-sm text-slate-500">Loading…</p>
        )}
      </div>

      <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
        <h2 className="text-sm font-semibold text-amber-900">
          Legacy admin console
          <span className="ml-2 rounded-full bg-amber-200 px-2 py-0.5 text-xs font-medium text-amber-900">
            legacy
          </span>
        </h2>
        <p className="mt-2 text-sm text-amber-900">
          Corpus and tenant administration runs in a separate, deliberately old-style console —
          server-rendered JSP with jQuery and Bootstrap, served by the retrieval service. It is
          kept as an honest mixed-technology integration exercise (see ARCHITECTURE.md §10) and asks
          for its own credentials (HTTP Basic; dev default <code>admin / scriptorium-dev</code>).
        </p>
        <a
          href={LEGACY_ADMIN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block rounded-md bg-amber-800 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
        >
          Open legacy console
          <span className="sr-only"> (opens in a new tab)</span>
        </a>
      </div>
    </section>
  );
}
