// Geometry of the phone-layout check (tools/checks/check_mobile.mjs, docs/mobile.md).
// Pure functions on plain boxes {left, top, right, bottom, width, height}, in CSS px.
// The check loads this file in the page before measure.js; tests/js/check-mobile.test.mjs
// loads it in Node.
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CheckMobileGeometry = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const TOLERANCE = 1; // px: sub-pixel rounding of the layout
  const TARGET_MIN = 24; // px: WCAG 2.5.8 Target Size (Minimum)
  const TEXT_MIN = 12; // px: smallest text size
  const HEADER_MAX = 0.2; // share of the first screen the fixed header may cover

  function box(left, top, width, height) {
    return { left, top, right: left + width, bottom: top + height, width, height };
  }

  function fromRect(r) {
    return box(r.left, r.top, r.width, r.height);
  }

  function intersect(a, b) {
    const left = Math.max(a.left, b.left);
    const right = Math.min(a.right, b.right);
    const top = Math.max(a.top, b.top);
    const bottom = Math.min(a.bottom, b.bottom);
    if (right <= left || bottom <= top) return null;
    return box(left, top, right - left, bottom - top);
  }

  function area(b) {
    return b ? b.width * b.height : 0;
  }

  // How far a box goes past the left and right edges of a viewport `width` px wide.
  function pastEdges(b, width, tolerance = TOLERANCE) {
    const left = b.left < -tolerance ? -b.left : 0;
    const right = b.right > width + tolerance ? b.right - width : 0;
    return { left, right, any: left > 0 || right > 0 };
  }

  // A box is inside the viewport when no side is more than `tolerance` px out.
  function insideViewport(b, width, height, tolerance = TOLERANCE) {
    return b.left >= -tolerance && b.top >= -tolerance
      && b.right <= width + tolerance && b.bottom <= height + tolerance;
  }

  // Two text boxes overlap when they share more than a sliver: the glyph boxes of tight
  // lines touch or cross by a pixel or two without hiding any text.
  function textOverlap(a, b, minSide = 3, minShare = 0.2) {
    const common = intersect(a, b);
    if (!common || common.width < minSide || common.height < minSide) return null;
    return area(common) >= minShare * Math.min(area(a), area(b)) ? common : null;
  }

  // Pairs of overlapping boxes among `items` ({box, ...}), found with a sweep on `top`.
  // `related(a, b)` skips pairs that may overlap (an element and its descendant).
  function overlappingPairs(items, related) {
    const sorted = items.slice().sort((a, b) => a.box.top - b.box.top);
    const pairs = [];
    for (let i = 0; i < sorted.length; i += 1) {
      const a = sorted[i];
      for (let j = i + 1; j < sorted.length && sorted[j].box.top < a.box.bottom; j += 1) {
        const b = sorted[j];
        if (related(a, b)) continue;
        const common = textOverlap(a.box, b.box);
        if (common) pairs.push([a, b, common]);
      }
    }
    return pairs;
  }

  function tooSmall(b, min = TARGET_MIN) {
    return b.width < min - 0.05 || b.height < min - 0.05;
  }

  function center(b) {
    return { x: (b.left + b.right) / 2, y: (b.top + b.bottom) / 2 };
  }

  // Share of a viewport `height` px tall covered by bands [top, bottom] (their union).
  function coverage(bands, height) {
    const spans = bands
      .map(([top, bottom]) => [Math.max(0, top), Math.min(height, bottom)])
      .filter(([top, bottom]) => bottom > top)
      .sort((a, b) => a[0] - b[0]);
    let covered = 0;
    let current = null;
    for (const [top, bottom] of spans) {
      if (!current || top > current[1]) {
        if (current) covered += current[1] - current[0];
        current = [top, bottom];
      } else {
        current[1] = Math.max(current[1], bottom);
      }
    }
    if (current) covered += current[1] - current[0];
    return covered / height;
  }

  function px(n) {
    return `${Math.round(n)} px`;
  }

  function size(b) {
    return `${Math.round(b.width)}×${Math.round(b.height)} px`;
  }

  return {
    TOLERANCE, TARGET_MIN, TEXT_MIN, HEADER_MAX,
    box, fromRect, intersect, area, pastEdges, insideViewport, textOverlap,
    overlappingPairs, tooSmall, center, coverage, px, size,
  };
});
