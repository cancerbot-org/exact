import { describe, expect, it } from "vitest";

import {
  DISTANCE_UNITS,
  baselineFilters,
  countActiveFilters,
  hasActiveFilters,
} from "./filters";

describe("baselineFilters", () => {
  it("carries the patient's country as the default", () => {
    // Reset must not clear it: the country is seeded from the profile, and
    // clearing would silently widen the search to every country in the
    // registry rather than restoring the default.
    expect(baselineFilters("US")).toEqual({ country: "US" });
  });

  it("is empty for a patient with no country", () => {
    expect(baselineFilters(undefined)).toEqual({});
  });
});

describe("countActiveFilters", () => {
  const base = baselineFilters("US");

  it("counts nothing when the panel matches the baseline", () => {
    expect(countActiveFilters({ country: "US" }, base)).toBe(0);
    expect(countActiveFilters({}, baselineFilters(undefined))).toBe(0);
  });

  it("does not count the patient's own country as a filter", () => {
    // The badge is meant to say "you narrowed this". A country the reader
    // never chose, that merely reflects where they are, is not that.
    expect(countActiveFilters({ country: "US", sponsor: "BioPharm" }, base)).toBe(1);
  });

  it("counts a country the reader chose over the seeded one", () => {
    expect(countActiveFilters({ country: "DE" }, base)).toBe(1);
  });

  it("counts each changed field once", () => {
    expect(
      countActiveFilters(
        {
          country: "US",
          searchTitle: "myeloma",
          phase: "PHASE3",
          validatedOnly: true,
          distance: 50,
        },
        base,
      ),
    ).toBe(4);
  });

  it("treats empty string, null and false as unset", () => {
    // A cleared text input hands back "" before the caller normalises it,
    // and an unticked checkbox is `false` — neither is a filter.
    expect(
      countActiveFilters(
        { country: "US", searchTitle: "", sponsor: undefined, validatedOnly: false },
        base,
      ),
    ).toBe(0);
  });

  it("ignores the tab and the sort control", () => {
    // Those live outside the panel; counting them would tick the badge up
    // when the reader switches tab, which they did not experience as
    // filtering.
    expect(
      countActiveFilters({ country: "US", type: "potential", sort: "distance" }, base),
    ).toBe(0);
  });

  it("ignores distance units, which cannot filter on their own", () => {
    expect(countActiveFilters({ country: "US", distanceUnits: "miles" }, base)).toBe(0);
    expect(
      countActiveFilters({ country: "US", distance: 50, distanceUnits: "miles" }, base),
    ).toBe(1);
  });
});

describe("hasActiveFilters", () => {
  it("is false at the baseline and true once something changes", () => {
    const base = baselineFilters("US");
    expect(hasActiveFilters({ country: "US" }, base)).toBe(false);
    expect(hasActiveFilters({ country: "US", register: "clinicaltrials.gov" }, base)).toBe(
      true,
    );
  });
});

describe("DISTANCE_UNITS", () => {
  it("sends the values the backend compares against", () => {
    // `by_distance` checks for `miles` and treats anything else as km. CB
    // sends `kilometers`, which filters correctly but is echoed back into
    // the response and rendered as "743 kilometers".
    expect(DISTANCE_UNITS.map((u) => u.value)).toEqual(["miles", "km"]);
  });
});
