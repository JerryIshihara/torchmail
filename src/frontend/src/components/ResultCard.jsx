import { countryFlag, prettyHiringParagraph, scorePillClass, scoreTextClass } from "../lib/formatters";

function Stat({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function ResultCard({ result, expanded, onToggle }) {
  const professor = result.professor ?? {};
  const university = result.university ?? {};
  const score = Number(result.composite_score ?? 0);
  const hasSource = Boolean(result.hiring_url);

  return (
    <article className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-3 p-4 sm:p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
              #{result.rank}
            </span>
            <h2 className="truncate text-base font-semibold text-slate-900 sm:text-lg">{professor.name}</h2>
            {result.is_priority_country ? (
              <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-blue-200">
                Priority Region
              </span>
            ) : null}
          </div>
          <div className={`rounded-full px-3 py-1 text-sm font-semibold ring-1 ${scorePillClass(score)}`}>
            Score {score.toFixed(1)}
          </div>
        </div>

        <p className="text-sm text-slate-700">
          {university.name || "Unknown university"} · {countryFlag(university.country_code)}{" "}
          {university.country_code || "N/A"}
        </p>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat label="Papers" value={result.paper_count ?? 0} />
          <Stat label="Citations" value={result.total_citations ?? 0} />
          <Stat label="Latest Date" value={result.latest_paper_date || "N/A"} />
          <Stat label="Score Band" value={<span className={scoreTextClass(score)}>{score.toFixed(1)}</span>} />
        </div>

        <button
          type="button"
          className="inline-flex w-fit items-center rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-500"
          onClick={onToggle}
          aria-expanded={expanded}
        >
          {expanded ? "Hide details" : "Show details"}
        </button>
      </div>

      {expanded ? (
        <div className="border-t border-slate-200 bg-slate-50 p-4 sm:p-5">
          <div className="space-y-2 text-sm text-slate-700">
            <p>
              <span className="font-semibold text-slate-900">ORCID:</span> {professor.orcid || "N/A"}
            </p>
            <p>
              <span className="font-semibold text-slate-900">OpenAlex:</span> {professor.openalex_id || "N/A"}
            </p>
            <p>
              <span className="font-semibold text-slate-900">Latest paper:</span>{" "}
              {result.latest_paper_title || "No recent paper title available"}
            </p>
            <p>
              <span className="font-semibold text-slate-900">Composite score breakdown:</span> 40% relevance, 30%
              activity, 20% citations, 10% recency
              {result.is_priority_country ? ", plus region-priority boost." : "."}
            </p>
          </div>

          <figure className="mt-4 rounded-lg border-l-4 border-blue-300 bg-white p-4">
            <blockquote className="font-serif text-sm leading-relaxed text-slate-800">
              “{prettyHiringParagraph(result.hiring_paragraph)}”
            </blockquote>
            <figcaption className="mt-3 text-xs text-slate-600">
              {hasSource ? (
                <a
                  href={result.hiring_url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1 text-blue-700 underline hover:text-blue-800"
                >
                  Source link
                  <span aria-hidden="true">↗</span>
                </a>
              ) : (
                "No source URL available yet."
              )}
            </figcaption>
          </figure>
        </div>
      ) : null}
    </article>
  );
}
