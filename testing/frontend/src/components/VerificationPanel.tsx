import VerdictBadge from "./VerdictBadge";
import type { Verification } from "../lib/api";

const asArray = (citations: Verification["citations"]) => {
  if (!citations) return [];
  return citations.map((entry) => {
    if (typeof entry === "string") {
      return { title: entry, url: entry };
    }
    return {
      title: entry.title || entry.url || "Source",
      url: entry.url || "",
    };
  });
};

export default function VerificationPanel({ verification }: { verification?: Verification | null }) {
  if (!verification) {
    return (
      <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        No verification available yet.
      </div>
    );
  }

  const citations = asArray(verification.citations);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-3">
        <VerdictBadge verdict={verification.verdict} />
        {typeof verification.truth_score === "number" && (
          <span className="text-xs font-semibold text-slate-600">Truth Score: {verification.truth_score.toFixed(2)}</span>
        )}
        {verification.confidence && (
          <span className="text-xs font-semibold text-slate-600">Confidence: {verification.confidence}</span>
        )}
        {verification.cached !== undefined && (
          <span className="text-xs font-semibold text-slate-600">Cached: {verification.cached ? "true" : "false"}</span>
        )}
      </div>
      {verification.explanation && (
        <p className="mt-3 text-sm text-slate-700">{verification.explanation}</p>
      )}
      {citations.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Citations</p>
          <ul className="mt-2 space-y-1 text-sm">
            {citations.map((citation, idx) => (
              <li key={`${citation.url}-${idx}`}>
                <a className="text-blue-600 hover:underline" href={citation.url} target="_blank" rel="noreferrer">
                  {citation.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
