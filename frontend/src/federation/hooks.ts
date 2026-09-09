// TanStack Query hooks for the EXACT API. Keys are stable so multiple
// `TrialMatches` instances mounted in the same host share the cache
// (e.g. mounting two filtered views with the same patient doesn't
// re-request).
import {
  keepPreviousData,
  useQuery,
  type UseQueryResult,
} from "@tanstack/react-query";
import type { AxiosInstance } from "axios";

import { fetchFormSettings, fetchTrialDetail, fetchTrials } from "./api";
import type {
  FilterState,
  PatientInfo,
  TrialDetailResponse,
  TrialsResponse,
} from "./types";

interface UseTrialsArgs {
  apiClient: AxiosInstance;
  patientInfo?: PatientInfo | null;
  personId?: string | number;
  filters?: FilterState;
  /** 1-indexed page. */
  page?: number;
  /** Rows per page. */
  limit?: number;
  /** Skip the query until the host has a patient context. Without
   *  patient context the response would be a public/unscoped trial
   *  list — usually not what a TrialMatches mount wants. */
  enabled?: boolean;
}

export function useTrials({
  apiClient,
  patientInfo,
  personId,
  filters,
  page = 1,
  limit,
  enabled = true,
}: UseTrialsArgs): UseQueryResult<TrialsResponse> {
  return useQuery({
    queryKey: [
      "exact-trials",
      personId ?? null,
      patientInfo ?? null,
      filters ?? null,
      page,
      limit ?? null,
    ],
    queryFn: () =>
      fetchTrials({ apiClient, patientInfo, personId, filters, page, limit }),
    // Paged, not infinite: CB paginates by number and so does this now, and
    // an infinite list cannot show per-tab totals or jump to a page. Previous
    // data is kept across page/filter changes so the list does not blank out
    // between requests — CB does the same (`keepPreviousData` in useTrials).
    placeholderData: keepPreviousData,
    enabled: enabled && (patientInfo != null || personId != null),
    staleTime: 30_000,
  });
}

interface UseTrialDetailArgs {
  apiClient: AxiosInstance;
  trialId: number | string;
  patientInfo?: PatientInfo | null;
  personId?: string | number;
  filters?: FilterState;
  enabled?: boolean;
}

export function useTrialDetail({
  apiClient,
  trialId,
  patientInfo,
  personId,
  filters,
  enabled = true,
}: UseTrialDetailArgs): UseQueryResult<TrialDetailResponse> {
  return useQuery({
    queryKey: [
      "exact-trial-detail",
      trialId,
      personId ?? null,
      patientInfo ?? null,
      filters ?? null,
    ],
    queryFn: () => fetchTrialDetail({ apiClient, trialId, patientInfo, personId, filters }),
    enabled: enabled && trialId != null,
    staleTime: 30_000,
  });
}

export function useFormSettings(
  apiClient: AxiosInstance,
  diseaseCode?: string,
): UseQueryResult<Record<string, { options: { value: string; label: string }[] }>> {
  return useQuery({
    queryKey: ["exact-form-settings", diseaseCode ?? null],
    queryFn: () => fetchFormSettings(apiClient, diseaseCode),
    staleTime: 5 * 60_000,
  });
}
