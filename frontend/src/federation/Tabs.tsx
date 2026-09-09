// Tab bar over the trial list, mirroring CB's `TabButton` row on Your
// Trials. Structure lives in `exact.css` (`.exact-tabs*`).
import { TABS, tabCount, type TabValue } from "./listChrome";
import type { TabCounts } from "./types";

interface Props {
  active: TabValue;
  onChange: (tab: TabValue) => void;
  /** Server-side totals over the whole matched corpus. Absent when the
   *  server could not judge — see `tabCount`. */
  counts?: TabCounts;
  /** `itemsTotalCount` of the current response, used only to label the
   *  default tab when the server sent no counts and that tab is the one
   *  being listed. */
  activeTabTotal: number | null;
}

export function Tabs({ active, onChange, counts, activeTabTotal }: Props) {
  return (
    <div className="exact-tabs" role="tablist">
      {TABS.map((tab) => {
        const isActive = tab.value === active;
        const count = tabCount(
          tab.value,
          counts,
          // Only the active tab's own total is meaningful as a fallback;
          // labelling an inactive tab with the active tab's count would be
          // a plain lie.
          isActive ? activeTabTotal : null,
        );
        return (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={`exact-tab${isActive ? " is-active" : ""}`}
            onClick={() => onChange(tab.value)}
          >
            <span className="exact-tab__label">{tab.label}</span>
            {count != null ? (
              <span className="exact-tab__count">{count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
