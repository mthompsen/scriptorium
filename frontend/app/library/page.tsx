'use client';

import { useRouter } from 'next/navigation';
import { FormEvent, useCallback, useEffect, useState } from 'react';

import { api, API_BASE, ApiError, DocumentRow } from '@/lib/api';

const STATUS_STYLES: Record<string, string> = {
  indexed: 'bg-emerald-100 text-emerald-800',
  stored: 'bg-sky-100 text-sky-800',
  processing: 'bg-sky-100 text-sky-800',
  uploaded: 'bg-amber-100 text-amber-800',
  failed: 'bg-red-100 text-red-800',
};

export default function LibraryPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api<DocumentRow[]>('/documents'));
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        router.replace('/login');
      }
    }
  }, [router]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file || busy) {
      return;
    }
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append('file', file);
    try {
      const response = await fetch(`${API_BASE}/api/v1/documents`, {
        method: 'POST',
        credentials: 'include',
        body: form,
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { message?: string };
        throw new ApiError(response.status, body.message ?? response.statusText);
      }
      setFile(null);
      (event.target as HTMLFormElement).reset();
      await refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Library</h1>

      <form onSubmit={upload} className="flex items-center gap-3">
        <input
          type="file"
          accept=".pdf,.docx,.md,.markdown,.html,.txt"
          aria-label="Document file"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm"
        />
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {busy ? 'Uploading…' : 'Upload'}
        </button>
      </form>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300 text-slate-600">
            <th className="py-2 pr-4 font-medium">Title</th>
            <th className="py-2 pr-4 font-medium">Type</th>
            <th className="py-2 pr-4 font-medium">Status</th>
            <th className="py-2 font-medium">Uploaded</th>
          </tr>
        </thead>
        <tbody>
          {documents.length === 0 && (
            <tr>
              <td colSpan={4} className="py-6 text-slate-500">
                No documents yet — upload one above.
              </td>
            </tr>
          )}
          {documents.map((doc) => (
            <tr key={doc.id} className="border-b border-slate-100">
              <td className="py-2 pr-4">{doc.title}</td>
              <td className="py-2 pr-4 text-slate-600">{doc.mime_type}</td>
              <td className="py-2 pr-4">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[doc.status] ?? 'bg-slate-100 text-slate-700'}`}
                >
                  {doc.status}
                </span>
              </td>
              <td className="py-2 text-slate-600">{new Date(doc.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
