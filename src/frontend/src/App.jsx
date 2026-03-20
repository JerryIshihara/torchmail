import { useMemo, useState } from "react";

import ResultCard from "./components/ResultCard";

const SEARCH_PLACEHOLDER = "e.g. bio-engineering in genome analysis";

function apiBaseUrl() {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  const raw = typeof fromEnv === "string" ? fromEnv.trim() : "";
  if (!raw) {
    return "";
  }
  return raw.replace(/\/+$/, "");
}

function Spinner() {
  return (
    <div className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
  );
}

function LoadingState() {
  return (
    <div className="space-y-3">
      {[...Array(3)].map((_, idx) => (
        <div key={idx} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="h-5 w-1/3 animate-pulse rounded bg-slate-200" />
          <div className="mt-3 h-4 w-2/3 animate-pulse rounded bg-slate-200" />
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {[...Array(4)].map((__, statIdx) => (
              <div key={statIdx} className="h-14 animate-pulse rounded bg-slate-100" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedIds, setExpandedIds] = useState(new Set());

  const hasResults = Boolean(results?.results?.length);
  const emptyResults = results && !hasResults;

  const endpoint = useMemo(() => `${apiBaseUrl()}/api/search`, []);

  const onSearch = async (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError("Please enter a research topic.");
      return;
    }

    setIsLoading(true);
    setError("");
    setResults(null);
    setExpandedIds(new Set());

    try {
      const params = new URLSearchParams({ q: trimmed });
      const response = await fetch(`${endpoint}?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`Search failed (${response.status})`);
      }
      const payload = await response.json();
      setResults(payload);
      if (payload.results?.length) {
        setExpandedIds(new Set([payload.results[0].id]));
      }
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Backend unreachable.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleResult = (id) => {
    setExpandedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">TorchMail Research Lab Search</h1>
          <p className="mt-2 text-sm text-slate-600 sm:text-base">
            Find top opportunities globally with exact hiring quotes and source links.
          </p>
        </header>

        <form
          onSubmit={onSearch}
          className="mx-auto mb-6 flex w-full max-w-3xl flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row"
          aria-label="Search for research opportunities"
        >
          <label htmlFor="query" className="sr-only">
            Research topic
          </label>
          <input
            id="query"
            name="query"
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={SEARCH_PLACEHOLDER}
            className="w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isLoading ? <Spinner /> : null}
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        {error ? (
          <p role="alert" className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </p>
        ) : null}

        {isLoading ? <LoadingState /> : null}

        {results ? (
          <section aria-live="polite" className="space-y-4">
            <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
              <span className="font-semibold text-slate-900">{results.result_count}</span> results for{" "}
              <span className="font-semibold text-slate-900">&ldquo;{results.query}&rdquo;</span>
              {" · "}
              <span>{results.priority_count} priority-region</span>
              {" · "}
              <span>{results.other_count} other regions</span>
              {" · "}
              <span>{results.from_cache ? "cached" : "fresh"}</span>
            </div>

            {emptyResults ? (
              <p className="rounded-xl border border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-600 shadow-sm">
                No results found. Try a broader topic.
              </p>
            ) : null}

            {hasResults ? (
              <ul className="space-y-3" aria-label="Search results">
                {results.results.map((result) => (
                  <li key={result.id}>
                    <ResultCard
                      result={result}
                      expanded={expandedIds.has(result.id)}
                      onToggle={() => toggleResult(result.id)}
                    />
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}
      </div>
    </main>
  );
}
