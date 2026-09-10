// Pure logic behind the filter panel: what counts as an active filter, and
// what "reset" means. Kept out of the component so the node-environment
// suite can test it (see vitest.config.ts, and #426 for the component-level
// gap).

import type { FilterState } from "./types";

export interface DistanceUnitOption {
  value: "km" | "miles";
  label: string;
}

/** The wire values `by_distance` understands. It compares against `miles`
 *  and treats everything else as kilometres, so CB's `kilometers` works but
 *  is echoed back verbatim into the response's `distanceUnits` and would be
 *  rendered as "743 kilometers". Send `km`. */
export const DISTANCE_UNITS: DistanceUnitOption[] = [
  { value: "miles", label: "miles" },
  { value: "km", label: "km" },
];

/** Filters the panel owns. `type` and `sort` are excluded on purpose: the
 *  tab bar and the sort control own those, and counting them would make the
 *  "Filters (N)" badge tick up when the user switches tab. */
const PANEL_FIELDS = [
  "searchTitle",
  "searchTreatment",
  "sponsor",
  "trialType",
  "trialPurpose",
  "recruitmentStatus",
  "phase",
  "register",
  "lastUpdate",
  "distance",
  // No control of their own — `country` is seeded from the patient, and
  // these three can only arrive through the host's `initialFilters`. They
  // are counted and cleared all the same, so the badge cannot read 0 while
  // a filter is running and Reset cannot leave one behind.
  "country",
  "region",
  "studyType",
  "validatedOnly",
] as const;

export type PanelField = (typeof PANEL_FIELDS)[number];

/** The state the panel resets to.
 *
 *  Not simply `{}`: `country` is seeded from the patient's own profile, so
 *  clearing it would silently widen the search to every country rather than
 *  restoring the default. The baseline carries whatever the patient implies.
 */
export function baselineFilters(
  patientCountry: string | undefined,
  initialFilters?: FilterState,
): FilterState {
  // The host's own initial filters are part of the baseline, not something
  // Reset throws away: a host that mounts the remote already scoped to a
  // register or a recruitment status means that scope to survive the button.
  const base: FilterState = { ...initialFilters };
  // The patient's country wins over a host default, because it is the more
  // specific fact — but only when there is one.
  if (patientCountry) base.country = patientCountry;
  return base;
}

function isEmpty(value: unknown): boolean {
  return value === undefined || value === null || value === "" || value === false;
}

/** A distance of 0 is not a filter: the backend gates on
 *  `if study_info.distance:`, so zero applies no limit. The control cannot
 *  produce one, but a host can pass one through `initialFilters`, and a
 *  badge counting it would claim a narrowing that never happened. */
function isInactive(field: PanelField, value: unknown): boolean {
  if (field === "distance") return isEmpty(value) || value === 0;
  return isEmpty(value);
}

/** How many filters the user has actually changed — the number CB shows on
 *  its Filters button (its own count comes from the server, which knows the
 *  stored defaults; here the baseline stands in for them).
 *
 *  Compared against the baseline rather than against emptiness so a country
 *  that merely matches the patient's own does not read as a filter the user
 *  applied. `distanceUnits` is not counted: it qualifies `distance` and
 *  cannot be set without it. */
export function countActiveFilters(
  filters: FilterState,
  baseline: FilterState,
): number {
  return PANEL_FIELDS.reduce((count, field) => {
    const value = filters[field];
    const base = baseline[field];
    if (isInactive(field, value) && isInactive(field, base)) return count;
    return value === base ? count : count + 1;
  }, 0);
}

/** Whether the panel is showing anything other than the baseline — drives
 *  whether Reset is worth offering. */
export function hasActiveFilters(
  filters: FilterState,
  baseline: FilterState,
): boolean {
  return countActiveFilters(filters, baseline) > 0;
}
