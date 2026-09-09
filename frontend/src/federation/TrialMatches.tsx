// Federated `./TrialMatches` export (#104, part of #101). Renders the
// patient's trial matches grouped by `matchingType`, with a filter bar,
// inline detail view, and host-agnostic axios injection. The host
// supplies either `patientInfo` (inline payload — matches the existing
// CB contract) or `personId` (CTOMOP federation path added in #102).
import { useEffect, useMemo, useState, useRef } from "react";

function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState<T>(value);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setDebounced(value), delay);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [value, delay]);
  return debounced;
}
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { FilterBar } from "./FilterBar";
import { TrialCard } from "./TrialCard";
import { TrialDetailPage } from "./TrialDetailPage";
import { Pagination } from "./Pagination";
import { SortControl } from "./SortControl";
import { Tabs } from "./Tabs";
import {
  DEFAULT_SORT,
  PAGE_SIZE,
  TABS,
  clampPage,
  totalPages,
  type TabValue,
} from "./listChrome";
import { useTrials } from "./hooks";
import { injectStyles } from "./injectStyles";
import type { FilterState, TrialMatch, TrialMatchesProps } from "./types";

function TrialMatchesInner({
  apiClient,
  patientInfo,
  personId,
  initialFilters,
  onTrialSelect,
}: Omit<TrialMatchesProps, "queryClient">) {
  useEffect(() => {
    injectStyles();
  }, []);

  const [filters, setFilters] = useState<FilterState>(initialFilters ?? {});
  const [selectedTrial, setSelectedTrial] = useState<TrialMatch | null>(null);
  const [activeTab, setActiveTab] = useState<TabValue>("eligible_and_potential");
  const [sort, setSort] = useState<string>(initialFilters?.sort ?? DEFAULT_SORT);
  const [page, setPage] = useState(1);

  // Reset detail view when patient context changes so we don't keep a
  // stale trial open from a previous patient. We key on a stable derived
  // identifier (`personId` or the JSON-serialised payload) instead of the
  // `patientInfo` reference directly — otherwise a host that re-creates
  // the payload object on every render (the default in React without
  // `useMemo`) would collapse the detail view on every parent re-render.
  const patientInfoKey = useMemo(
    () => (patientInfo ? JSON.stringify(patientInfo) : null),
    [patientInfo],
  );
  useEffect(() => {
    setSelectedTrial(null);
    setPage(1);
  }, [personId, patientInfoKey]);

  // Auto-derive `country` from the patient profile. The country filter
  // was previously a dropdown but in practice was redundant — patients
  // are matched to trials in their home country. We sync on every
  // patient change (not just first mount) so swapping `patientInfo`
  // — e.g. picking another row in the dev harness — re-scopes the
  // trial list correctly. The equality guard prevents a `setFilters`
  // re-render storm when the patient's country is already the active
  // filter. `undefined` clears the param so a patient without a country
  // gets the disease-agnostic union, not a stale previous country.
  const patientCountry = useMemo(() => {
    const c = (patientInfo as Record<string, unknown> | null | undefined)?.["country"];
    return typeof c === "string" && c.trim() ? c.trim() : undefined;
  }, [patientInfo]);
  useEffect(() => {
    if (filters.country === patientCountry) return;
    setFilters((prev) => ({ ...prev, country: patientCountry }));
  }, [patientCountry, filters.country]);

  const debouncedTitle = useDebounced(filters.searchTitle, 400);
  const debouncedTreatment = useDebounced(filters.searchTreatment, 400);
  const debouncedDistance = useDebounced(filters.distance, 400);
  const debouncedDistanceUnits = useDebounced(filters.distanceUnits, 400);
  const activeTabDef = TABS.find((t) => t.value === activeTab) ?? TABS[0];
  const queryFilters = useMemo(
    () => ({
      ...filters,
      searchTitle: debouncedTitle,
      searchTreatment: debouncedTreatment,
      distance: debouncedDistance,
      distanceUnits: debouncedDistanceUnits,
      type: activeTabDef.param,
      sort: sort as FilterState["sort"],
    }),
    [
      filters,
      debouncedTitle,
      debouncedTreatment,
      debouncedDistance,
      debouncedDistanceUnits,
      activeTabDef.param,
      sort,
    ],
  );

  const query = useTrials({
    apiClient,
    patientInfo,
    personId,
    filters: queryFilters,
    page,
    limit: PAGE_SIZE,
  });

  const trials = query.data?.results ?? [];
  const totalCount = query.data?.itemsTotalCount ?? null;
  const tabCounts = query.data?.tabCounts;
  const pageCount = totalPages(totalCount ?? 0);

  // A filter or tab change can shrink the result set under the current page.
  // Snap back rather than showing an empty page with no way forward.
  useEffect(() => {
    if (pageCount > 0 && page > pageCount) setPage(clampPage(page, pageCount));
  }, [page, pageCount]);

  const handleTabChange = (next: TabValue) => {
    setActiveTab(next);
    setPage(1);
  };

  const handleSortChange = (next: string) => {
    setSort(next);
    setPage(1);
  };

  const handleFiltersChange = (next: FilterState) => {
    setFilters(next);
    setPage(1);
  };

  const diseaseCode = useMemo(() => {
    const d = (patientInfo as Record<string, unknown> | null | undefined)?.["disease"];
    return typeof d === "string" ? d : undefined;
  }, [patientInfo]);

  const handleSelect = (trial: TrialMatch) => {
    setSelectedTrial(trial);
    onTrialSelect?.(trial);
  };

  // When the detail view opens, push a synthetic history entry so the
  // browser ← back button returns to the trial list instead of navigating
  // to the previous host page. The popstate listener tears itself down
  // when the detail closes (effect cleanup) or when the patient context
  // resets (selectedTrial becomes null via the reset effect above).
  useEffect(() => {
    if (!selectedTrial) return;
    window.history.pushState({ exactTrialDetail: selectedTrial.trialId }, "");
    const handler = () => setSelectedTrial(null);
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, [selectedTrial]);

  // Selecting a trial swaps the whole view for the in-remote detail page
  // (CB navigates to its own `/t/:id`; the remote owns the detail itself).
  // `onBack` calls history.back() so the synthetic entry is consumed and
  // the popstate listener above fires setSelectedTrial(null).
  if (selectedTrial) {
    return (
      <TrialDetailPage
        apiClient={apiClient}
        trialId={selectedTrial.trialId}
        patientInfo={patientInfo}
        personId={personId}
        filters={filters}
        onBack={() => window.history.back()}
      />
    );
  }

  return (
    <div className="exact-root exact-list" style={{ padding: "1rem" }}>
      <h1 className="exact-list__title">Your Trials</h1>

      <Tabs
        active={activeTab}
        onChange={handleTabChange}
        counts={tabCounts}
        activeTabTotal={totalCount}
      />

      <div className="exact-list__controls">
        <SortControl value={sort} onChange={handleSortChange} />
      </div>

      <FilterBar
        apiClient={apiClient}
        filters={filters}
        onChange={handleFiltersChange}
        diseaseCode={diseaseCode}
      />

      {query.isLoading ? (
        <p style={{ color: "var(--exact-color-text-muted)" }}>Loading trials…</p>
      ) : null}

      {query.isError ? (
        <p style={{ color: "var(--exact-color-not-eligible)" }}>
          Failed to load trials: {(query.error as Error)?.message ?? "unknown error"}
        </p>
      ) : null}

      {/* Kept mounted while a page or filter change is in flight, because
          `keepPreviousData` leaves the previous rows on screen: without a
          signal the list looks stale-but-current. CB shows the same
          floating "Updating…" pill. */}
      {query.isFetching && !query.isLoading ? (
        <div className="exact-list__updating" role="status">
          Updating…
        </div>
      ) : null}

      <div
        className={`exact-list__rows${query.isFetching ? " is-fetching" : ""}`}
      >
        {trials.map((t) => (
          <TrialCard key={t.trialId} trial={t} onSelect={handleSelect} />
        ))}
      </div>

      {!query.isLoading && patientInfo == null && personId == null ? (
        <p style={{ color: "var(--exact-color-text-muted)" }}>
          Pass a <code>patientInfo</code> payload or <code>personId</code> to load
          trial matches.
        </p>
      ) : null}

      {!query.isLoading &&
      (patientInfo != null || personId != null) &&
      trials.length === 0 ? (
        <p style={{ color: "var(--exact-color-text-muted)" }}>No trials found</p>
      ) : null}

      <Pagination
        page={page}
        pageCount={pageCount}
        onChange={setPage}
      />
    </div>
  );
}

export function TrialMatches(props: TrialMatchesProps) {
  // If the host provides a QueryClient we use it; otherwise spin up our
  // own. Keeping the local one stable across renders avoids React Query's
  // re-mount thrash when the parent re-renders for unrelated reasons.
  const [ownClient] = useState(() => new QueryClient());
  const client = props.queryClient ?? ownClient;

  return (
    <QueryClientProvider client={client}>
      <TrialMatchesInner {...props} />
    </QueryClientProvider>
  );
}

export default TrialMatches;
