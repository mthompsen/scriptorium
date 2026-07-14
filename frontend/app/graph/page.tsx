'use client';

import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';

import { api, ApiError, GraphEntityHit, Neighborhood } from '@/lib/api';

// Canvas rendering — client-only.
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

interface ForceData {
  nodes: { id: string; name: string; type: string }[];
  links: { source: string; target: string; relation: string }[];
}

export default function GraphPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<GraphEntityHit[]>([]);
  const [data, setData] = useState<ForceData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api('/auth/me').catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 401) {
        router.replace('/login');
      }
    });
  }, [router]);

  async function search(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const result = await api<{ entities: GraphEntityHit[] }>(
        `/graph/search?q=${encodeURIComponent(query)}`,
      );
      setHits(result.entities);
      if (result.entities.length === 0) {
        setData(null);
        setError('No entities matched — upload documents or try another name.');
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Search failed');
    }
  }

  async function explore(entityId: string, entityName: string) {
    setError(null);
    setSelected(entityName);
    try {
      const neighborhood = await api<Neighborhood>(`/graph/entity/${entityId}/neighborhood`);
      setData({
        nodes: neighborhood.nodes,
        links: neighborhood.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          relation: edge.relation,
        })),
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load neighborhood');
    }
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Graph Explorer</h1>
      <p className="text-sm text-slate-600">
        Entities and relations extracted from your documents. Search, then click a node to walk
        the graph.
      </p>

      <form onSubmit={search} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search entities (e.g. a company, policy, or system)…"
          aria-label="Entity search"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={!query.trim()}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          Search
        </button>
      </form>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {hits.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {hits.map((hit) => (
            <li key={hit.id}>
              <button
                onClick={() => explore(hit.id, hit.name)}
                className={`rounded-full border px-3 py-1 text-xs font-medium hover:bg-slate-100 ${
                  selected === hit.name ? 'border-slate-900 bg-slate-100' : 'border-slate-300'
                }`}
              >
                {hit.name} <span className="text-slate-500">({hit.type})</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {data && (
        <div className="h-[60vh] overflow-hidden rounded-md border border-slate-200 bg-white">
          <ForceGraph2D
            graphData={data}
            nodeId="id"
            nodeLabel={(node) => `${(node as { name: string }).name}`}
            nodeAutoColorBy="type"
            linkLabel={(link) => (link as { relation: string }).relation}
            linkDirectionalArrowLength={4}
            onNodeClick={(node) => {
              const clicked = node as { id: string; name: string };
              void explore(clicked.id, clicked.name);
            }}
          />
        </div>
      )}
    </section>
  );
}
