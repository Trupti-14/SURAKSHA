function getField(item, candidates, fallback) {
  if (!item || typeof item !== "object") {
    return fallback;
  }

  const key = candidates.find(
    (candidate) =>
      typeof item[candidate] === "string" && item[candidate].trim().length > 0,
  );

  return key ? item[key] : fallback;
}

export default function CircularCompare({ gap }) {
  if (!gap) {
    return null;
  }

  const existingReference = getField(
    gap,
    ["old_requirement", "old_policy", "existing_requirement", "current_policy"],
    "Existing approved reference was not specified in the response.",
  );
  const newRequirement = getField(
    gap,
    ["new_requirement", "new_policy", "requirement", "obligation", "description"],
    "New circular requirement was not specified in the response.",
  );
  const policyGap = getField(
    gap,
    ["policy_gap", "detected_gap", "gap", "summary", "description"],
    "Gap details were not specified in the response.",
  );

  return (
    <section className="rounded-xl border border-slate-800/80 bg-[#0f1b2d] shadow-[0_18px_44px_rgba(2,6,23,0.24)]">
      <div className="border-b border-slate-800/80 px-5 py-4">
        <h2 className="text-base font-semibold tracking-wide text-slate-50">
          First Gap Preview
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          A quick view of how the new circular differs from approved references.
        </p>
      </div>

      <div className="grid gap-4 p-4 lg:grid-cols-3">
        <div className="rounded-lg border border-slate-800/80 bg-[#0a1627] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Existing Reference
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {existingReference}
          </p>
        </div>

        <div className="rounded-lg border border-sky-400/25 bg-sky-500/[0.08] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-sky-300">
            New Requirement
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-100">
            {newRequirement}
          </p>
        </div>

        <div className="rounded-lg border border-amber-400/25 bg-amber-500/[0.08] p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-300">
            Gap Detected
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-100">
            {policyGap}
          </p>
        </div>
      </div>
    </section>
  );
}
