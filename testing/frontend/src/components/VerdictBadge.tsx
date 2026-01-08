type Props = {
  verdict?: string | null;
};

const styles: Record<string, string> = {
  true: "bg-emerald-100 text-emerald-700",
  false: "bg-rose-100 text-rose-700",
  misleading: "bg-amber-100 text-amber-700",
  unknown: "bg-slate-200 text-slate-700",
  unverified: "bg-slate-200 text-slate-700",
};

export default function VerdictBadge({ verdict }: Props) {
  const normalized = (verdict || "unknown").toLowerCase();
  const label = normalized.toUpperCase();
  const cls = styles[normalized] || styles.unknown;

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${cls}`}>
      {label}
    </span>
  );
}
