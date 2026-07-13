import Link from 'next/link';

export default function Home() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Scriptorium</h1>
      <p className="max-w-prose text-slate-700">
        Enterprise knowledge intelligence platform. Upload documents to the library, then ask
        questions in chat. Answers are stubbed until the RAG core lands in M2.
      </p>
      <div className="flex gap-3">
        <Link
          href="/login"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Sign in
        </Link>
        <Link
          href="/library"
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-100"
        >
          Library
        </Link>
      </div>
    </section>
  );
}
