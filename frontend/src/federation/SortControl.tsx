// Sort dropdown, mirroring CB's `TrialsSortControl`. A native `<select>`
// rather than a styled listbox: the remote ships no component library, and
// a native control is keyboard- and screen-reader-correct for free.
import { sortOptionsFor } from "./listChrome";

interface Props {
  value: string;
  onChange: (next: string) => void;
}

export function SortControl({ value, onChange }: Props) {
  return (
    <label className="exact-sort">
      <span className="exact-sort__label">Sort</span>
      <select
        className="exact-sort__select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {sortOptionsFor(value).map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
