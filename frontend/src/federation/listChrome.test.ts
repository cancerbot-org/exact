import { describe, expect, it } from "vitest";

import {
  PAGE_SIZE,
  TABS,
  clampPage,
  getPageNumbers,
  tabCount,
  totalPages,
} from "./listChrome";

describe("getPageNumbers", () => {
  // Ported from CB `pages/Trials.tsx`; these lock the port so the two
  // paginations cannot drift apart silently.
  it("lists every page while there are seven or fewer", () => {
    expect(getPageNumbers(1, 7)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(getPageNumbers(4, 4)).toEqual([1, 2, 3, 4]);
  });

  it("elides the tail when the current page is near the start", () => {
    expect(getPageNumbers(1, 20)).toEqual([1, 2, "…", 20]);
    expect(getPageNumbers(3, 20)).toEqual([1, 2, 3, 4, "…", 20]);
  });

  it("elides the head when the current page is near the end", () => {
    expect(getPageNumbers(20, 20)).toEqual([1, "…", 19, 20]);
  });

  it("elides both sides in the middle", () => {
    expect(getPageNumbers(10, 20)).toEqual([1, "…", 9, 10, 11, "…", 20]);
  });

  it("returns nothing when there are no pages", () => {
    expect(getPageNumbers(1, 0)).toEqual([]);
  });

  it("never repeats a page number", () => {
    // The window around the current page can otherwise collide with the
    // pinned first/last entries — at page 2 of 8 the window starts at 1,
    // and at page 7 it ends at 8.
    for (let total = 8; total <= 12; total++) {
      for (let page = 1; page <= total; page++) {
        const numbers = getPageNumbers(page, total).filter(
          (entry): entry is number => entry !== "…",
        );
        expect(new Set(numbers).size, `page ${page} of ${total}`).toBe(
          numbers.length,
        );
      }
    }
  });

  it("keeps the numbers ascending", () => {
    for (let page = 1; page <= 20; page++) {
      const numbers = getPageNumbers(page, 20).filter(
        (entry): entry is number => entry !== "…",
      );
      expect([...numbers].sort((a, b) => a - b), `page ${page}`).toEqual(numbers);
    }
  });

  it("always offers the current page as a target", () => {
    for (let page = 1; page <= 20; page++) {
      expect(getPageNumbers(page, 20), `page ${page}`).toContain(page);
    }
  });
});

describe("totalPages", () => {
  it("rounds up a partial last page", () => {
    expect(totalPages(1, 10)).toBe(1);
    expect(totalPages(10, 10)).toBe(1);
    expect(totalPages(11, 10)).toBe(2);
  });

  it("is zero for an empty result set", () => {
    expect(totalPages(0, 10)).toBe(0);
  });

  it("defaults to the page size the list requests", () => {
    expect(totalPages(PAGE_SIZE + 1)).toBe(2);
  });
});

describe("clampPage", () => {
  it("pulls an out-of-range page back into range", () => {
    // The case that matters: a filter change shrinks the result set while
    // the user is on page 9. Without the clamp the list shows an empty page
    // and the pagination row is gone, so there is no way back.
    expect(clampPage(9, 3)).toBe(3);
    expect(clampPage(0, 3)).toBe(1);
    expect(clampPage(-4, 3)).toBe(1);
  });

  it("leaves a valid page alone", () => {
    expect(clampPage(2, 3)).toBe(2);
  });

  it("does not clamp against a page count it does not have yet", () => {
    // Zero pages means the count has not arrived (or the set is empty).
    // Clamping against it would send the reader to page 0, or snap them to
    // page 1 on every first render before the response lands.
    expect(clampPage(5, 0)).toBe(5);
    // A junk page is still floored to 1, count or no count.
    expect(clampPage(Number.NaN, 0)).toBe(1);
  });
});

describe("tabCount", () => {
  const counts = { eligible: 7, potential: 12 };

  it("sums both buckets for the default tab", () => {
    expect(tabCount("eligible_and_potential", counts, 19)).toBe(19);
  });

  it("reads each bucket for its own tab", () => {
    expect(tabCount("eligible", counts, null)).toBe(7);
    expect(tabCount("potential", counts, null)).toBe(12);
  });

  it("returns null — not zero — when the server sent no counts", () => {
    // The server omits `tabCounts` when it had no patient context, or under
    // `?type=all`, because no per-row verdict was computed. Rendering "0"
    // there would state a clinical result nobody produced.
    expect(tabCount("eligible", undefined, 40)).toBeNull();
    expect(tabCount("potential", undefined, 40)).toBeNull();
  });

  it("falls back to the response total only for the tab being listed", () => {
    // The caller passes the total for the active tab and null for the rest,
    // so an inactive tab cannot be labelled with the active tab's number.
    expect(tabCount("eligible_and_potential", undefined, 40)).toBe(40);
    expect(tabCount("eligible_and_potential", undefined, null)).toBeNull();
  });
});

describe("TABS", () => {
  it("sends no type for the default tab", () => {
    // `eligible_and_potential` is a no-op server-side, identical to sending
    // no `type` at all — so the wire carries nothing rather than a value
    // that looks like it narrows something.
    expect(TABS[0].value).toBe("eligible_and_potential");
    expect(TABS[0].param).toBeUndefined();
  });

  it("offers no tab the server would reject", () => {
    // `favorites` and `my_trials` are 400s until PROMOP-backed state lands
    // in phase 2 (EXACT #417). A tab that cannot work must not be rendered.
    const params = TABS.map((tab) => tab.param);
    expect(params).not.toContain("favorites");
    expect(params).not.toContain("my_trials");
    expect(params).not.toContain("not_eligible");
  });
});
