// Pure logic behind the list chrome — tabs, sort options, pagination.
// Kept out of the components so it can be tested without rendering (the
// suite runs in a node environment; see vitest.config.ts).

import type { TabCounts } from "./types";

/** Rows per page. CB shows 10; the server's own default is 20. */
export const PAGE_SIZE = 10;

/** The tabs CB offers, minus the two that need per-user state.
 *
 *  CB's bar is Eligible / All Trials (admin) / Registered / Favorites.
 *  Registered and Favorites are per-user relations EXACT does not hold —
 *  the server rejects `?type=favorites` and `?type=my_trials` outright
 *  (EXACT #417) — so they arrive with the PROMOP-backed state adapter in
 *  phase 2 rather than being rendered as tabs that cannot work.
 *
 *  `eligible_and_potential` is CB's default tab. It is a no-op server-side,
 *  identical to sending no `type` at all, so it maps to `undefined` here
 *  rather than to a parameter that would suggest it narrows something. */
export type TabValue = "eligible_and_potential" | "eligible" | "potential" | "all";

export interface TabDef {
  value: TabValue;
  label: string;
  /** What goes on the wire; `undefined` means "send no `type`". */
  param?: "eligible" | "potential" | "all";
}

export const TABS: TabDef[] = [
  { value: "eligible_and_potential", label: "Eligible" },
  { value: "eligible", label: "Fully matched", param: "eligible" },
  { value: "potential", label: "Potential", param: "potential" },
];

/** The tab whose `param` matches a `type` the host passed in `initialFilters`.
 *  Falls back to the default tab for `undefined` and for values that are not
 *  tabs (`all` is a supported server value but is not offered as a tab). */
export function tabValueForType(type: string | undefined): TabValue {
  const match = TABS.find((tab) => tab.param === type);
  return match ? match.value : "eligible_and_potential";
}

/** The count to show next to a tab, or null when the server did not say.
 *
 *  Absence is not zero: the server omits `tabCounts` when it had no patient
 *  context, and under `?type=all`, because in both cases no per-row verdict
 *  was computed. Rendering a "0" there would state a clinical result nobody
 *  produced, so the caller shows nothing instead. */
export function tabCount(
  tab: TabValue,
  counts: TabCounts | undefined,
  itemsTotalCount: number | null,
): number | null {
  if (tab === "eligible_and_potential") {
    if (counts) return counts.eligible + counts.potential;
    // Without counts the total is only the whole corpus when this tab is
    // the active one; the caller passes null otherwise.
    return itemsTotalCount;
  }
  if (!counts) return null;
  return tab === "eligible" ? counts.eligible : counts.potential;
}

export interface SortOption {
  value: string;
  label: string;
}

/** CB's three, in CB's order. The server accepts more (`status`, `phase`,
 *  `updated`, `enrollment`, `patientBurdenScore`); those are not offered
 *  because CB does not offer them and parity is the point. */
export const SORT_OPTIONS: SortOption[] = [
  { value: "goodnessScore", label: "Sort By Suitability Score" },
  { value: "matchScore", label: "Sort by Matching Score" },
  { value: "distance", label: "Sort by Distance" },
];

export const DEFAULT_SORT = "goodnessScore";

/** The options to render, given the value the control is actually set to.
 *
 *  The server accepts more sort keys than CB offers (`status`, `phase`,
 *  `updated`, `enrollment`, `patientBurdenScore`). A host can pass one via
 *  `initialFilters.sort`, and a `<select>` whose value matches no `<option>`
 *  renders blank while the list is genuinely sorted that way — the control
 *  would be lying about what it is doing. Surface the value instead. */
export function sortOptionsFor(value: string): SortOption[] {
  if (SORT_OPTIONS.some((option) => option.value === value)) return SORT_OPTIONS;
  return [...SORT_OPTIONS, { value, label: `Sorted by ${value}` }];
}

/** Page numbers to render, with "…" where the run is broken.
 *
 *  Ported from CB `pages/Trials.tsx` so the two paginations look and behave
 *  the same: every page up to 7, otherwise first, last, the current page
 *  and its neighbours, with ellipses filling the gaps. */
export function getPageNumbers(
  currentPage: number,
  total: number,
): (number | "…")[] {
  const pages: (number | "…")[] = [];
  if (total <= 0) return pages;

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
    return pages;
  }

  pages.push(1);
  if (currentPage > 3) pages.push("…");

  for (
    let i = Math.max(2, currentPage - 1);
    i <= Math.min(total - 1, currentPage + 1);
    i++
  ) {
    pages.push(i);
  }

  if (currentPage < total - 2) pages.push("…");
  pages.push(total);
  return pages;
}
