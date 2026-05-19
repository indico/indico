// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {dropdownPositionStrategy, position} from './positioning';

function mockRect(el, {top, left, width, height}) {
  el.getBoundingClientRect = () => ({
    x: left,
    y: top,
    top,
    left,
    right: left + width,
    bottom: top + height,
    width,
    height,
    toJSON: () => ({}),
  });
}

function makeViewport({
  width = 1024,
  height = 768,
  scrollX = 0,
  scrollY = 0,
  visualViewport = null,
} = {}) {
  return {
    documentElement: {clientWidth: width, clientHeight: height},
    windowObj: {
      scrollX,
      scrollY,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    },
    visualViewport,
  };
}

function makeVisualViewport({offsetTop = 0, offsetLeft = 0, width, height} = {}) {
  return {
    offsetTop,
    offsetLeft,
    width,
    height,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  };
}

function parsePx(value) {
  const match = value.match(/^(-?[\d.]+)px$/);
  if (!match) {
    throw new Error(`Unexpected px value: ${value}`);
  }
  return parseFloat(match[1]);
}

describe('positioning', () => {
  let anchor, target, abort, originalRAF;

  beforeEach(() => {
    document.body.innerHTML = '<div id="anchor"></div><div id="target"></div>';
    anchor = document.getElementById('anchor');
    target = document.getElementById('target');

    originalRAF = global.requestAnimationFrame;
    global.requestAnimationFrame = cb => {
      cb();
      return 0;
    };
  });

  afterEach(() => {
    abort?.();
    abort = undefined;
    global.requestAnimationFrame = originalRAF;
  });

  describe('dropdownPositionStrategy — desktop happy paths', () => {
    it('places the target below the anchor when there is room', () => {
      mockRect(anchor, {top: 100, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      const cb = jest.fn();
      abort = position(target, anchor, dropdownPositionStrategy, cb, makeViewport());

      // anchorBottom = 130; flush-left to anchorLeft = 50
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(130);
      expect(parsePx(target.style.getPropertyValue('--target-left'))).toBe(50);
      expect(cb).toHaveBeenCalledWith(true);
    });

    it('places the target above the anchor when there is no room below', () => {
      mockRect(anchor, {top: 600, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      const cb = jest.fn();
      abort = position(target, anchor, dropdownPositionStrategy, cb, makeViewport());

      // Below: 630 + 200 = 830 > 768 → no fit
      // Above: anchorTop - targetHeight = 600 - 200 = 400
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(400);
      expect(cb).toHaveBeenCalledWith(false);
    });

    it('flushes the target to the right edge of the anchor when no room on the right', () => {
      mockRect(anchor, {top: 100, left: 900, width: 100, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      abort = position(target, anchor, dropdownPositionStrategy, undefined, makeViewport());

      // alignsPreferredSide: 900 + 200 = 1100 > 1024 → false
      // setLeft(anchorRight - targetWidth) = 1000 - 200 = 800
      expect(parsePx(target.style.getPropertyValue('--target-left'))).toBe(800);
    });

    it('sets anchor geometry custom properties so the target can match the anchor width', () => {
      mockRect(anchor, {top: 100, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 100, height: 100});

      abort = position(target, anchor, dropdownPositionStrategy, undefined, makeViewport());

      expect(target.style.getPropertyValue('--anchor-width')).toBe('200px');
      expect(target.style.getPropertyValue('--anchor-height')).toBe('30px');
    });
  });

  describe('dropdownPositionStrategy — re-aligns on scroll', () => {
    it('adjusts the target position by the scroll delta', () => {
      mockRect(anchor, {top: 100, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      const viewport = makeViewport();
      abort = position(target, anchor, dropdownPositionStrategy, undefined, viewport);

      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(130);

      // Simulate scroll: bump the windowObj scrollY and invoke the registered
      // scroll handler. positioning subtracts the delta so the target follows
      // the (now-shifted) anchor.
      viewport.windowObj.scrollY = 40;
      const scrollHandler = viewport.windowObj.addEventListener.mock.calls.find(
        ([eventName]) => eventName === 'scroll'
      )[1];
      scrollHandler();
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(90);
    });
  });

  describe('dropdownPositionStrategy — adjacency in edge cases', () => {
    // The dropdown is always glued to its anchor: either directly below
    // (setTop(anchorBottom)) or directly above (setTop(anchorTop - targetHeight)),
    // and flush-left (setLeft(anchorLeft)) or flush-right (setLeft(anchorRight -
    // targetWidth)). It may overflow the viewport when the anchor itself does
    // or the target is bigger than the available room on every side, but it
    // never visually detaches.

    it('places the target above when below does not fit', () => {
      // Anchor near the bottom of a small viewport.
      mockRect(anchor, {top: 700, left: 8, width: 350, height: 30});
      mockRect(target, {top: 0, left: 0, width: 350, height: 200});

      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({width: 375, height: 600})
      );

      // roomBelow = 600 - 730 = -130, roomAbove = 700 - 0 = 700.
      // fitsAbove → place above at anchorTop - targetHeight = 500.
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(500);
    });

    it('follows the anchor when it is partly above the viewport', () => {
      mockRect(anchor, {top: -100, left: 8, width: 350, height: 30});
      mockRect(target, {top: 0, left: 0, width: 350, height: 200});

      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({width: 375, height: 600})
      );

      // roomBelow = 600 - (-70) = 670, fits → place below at anchorBottom = -70.
      // The dropdown's top is negative (partially clipped at the top), but it
      // stays adjacent to the anchor so they move together on scroll.
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(-70);
    });

    it('follows the anchor when it is partly past the left edge', () => {
      mockRect(anchor, {top: 100, left: -50, width: 100, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      abort = position(target, anchor, dropdownPositionStrategy, undefined, makeViewport());

      // spaceForFlushLeft = 1024 - (-50) = 1074, fits → setLeft(anchorLeft) = -50.
      // The dropdown stays adjacent to the anchor's left edge.
      expect(parsePx(target.style.getPropertyValue('--target-left'))).toBe(-50);
    });

    it('uses the visible viewport rather than the layout viewport for fit checks', () => {
      // iOS Safari with the on-screen keyboard up: clientHeight reports the
      // full layout height, but the visual viewport is half that. The fit
      // check uses the visible area, so we correctly decide that below does
      // NOT fit and place the dropdown above.
      mockRect(anchor, {top: 100, left: 8, width: 350, height: 30});
      mockRect(target, {top: 0, left: 0, width: 350, height: 250});

      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({
          width: 375,
          height: 800,
          visualViewport: makeVisualViewport({width: 375, height: 300}),
        })
      );

      // Visible bottom = 0 + 300 = 300. anchorBottom = 130.
      // roomBelow = 300 - 130 = 170, roomAbove = 100 - 0 = 100.
      // Neither fits the 250px target. roomBelow > roomAbove → place below.
      // setTop(anchorBottom) = 130. (The dropdown overflows the keyboard zone
      // but its first ~170px is visible.)
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(130);
    });

    it('places flush-left when neither flush side fits the visible viewport', () => {
      // Combobox near the left edge of a narrow viewport with content wider
      // than the gap to either side.
      mockRect(anchor, {top: 100, left: 60, width: 100, height: 30});
      mockRect(target, {top: 0, left: 0, width: 250, height: 100});

      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({width: 280, height: 600})
      );

      // spaceForFlushLeft = 280 - 60 = 220, doesn't fit 250.
      // spaceForFlushRight = 160 - 0 = 160, doesn't fit 250.
      // spaceForFlushLeft > spaceForFlushRight → flush-left, overflow right.
      // setLeft(anchorLeft) = 60.
      expect(parsePx(target.style.getPropertyValue('--target-left'))).toBe(60);
    });

    it('places flush-right when flush-right fits but flush-left does not', () => {
      // Anchor near the right edge.
      mockRect(anchor, {top: 100, left: 900, width: 100, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      abort = position(target, anchor, dropdownPositionStrategy, undefined, makeViewport());

      // spaceForFlushLeft = 1024 - 900 = 124, doesn't fit 200.
      // spaceForFlushRight = 1000 - 0 = 1000, fits 200.
      // setLeft(anchorRight - targetWidth) = 1000 - 200 = 800.
      expect(parsePx(target.style.getPropertyValue('--target-left'))).toBe(800);
    });
  });

  describe('dropdownPositionStrategy — fuzz', () => {
    // Property-based exploration. The invariant we assert is:
    //   "the dropdown is adjacent to its anchor"
    // i.e., its top equals either anchorBottom (placed below) or
    // anchorTop - targetHeight (placed above), and its left equals
    // either anchorLeft (flush-left) or anchorRight - targetWidth
    // (flush-right). This must hold for every input — the dropdown
    // is allowed to overflow the viewport, but never to detach.

    function makeRng(seed) {
      // Linear-congruential PRNG. The `>>> 0` coercions keep the state in
      // an unsigned 32-bit range — canonical idiom, silence no-bitwise.
      // eslint-disable-next-line no-bitwise
      let s = seed >>> 0;
      return () => {
        // eslint-disable-next-line no-bitwise
        s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
        return s / 0x100000000;
      };
    }

    function rint(rng, min, max) {
      return Math.floor(rng() * (max - min + 1)) + min;
    }

    function runScenario(rng, withVisualViewport = false) {
      const viewportWidth = rint(rng, 320, 1920);
      const viewportHeight = rint(rng, 480, 1080);
      const anchorWidth = rint(rng, 80, 400);
      const anchorHeight = rint(rng, 20, 60);
      const anchorTop = rint(rng, -200, viewportHeight + 200);
      const anchorLeft = rint(rng, -200, viewportWidth + 200);
      const targetWidth = anchorWidth + rint(rng, 0, 200);
      const targetHeight = rint(rng, 50, 500);

      const viewportOptions = {width: viewportWidth, height: viewportHeight};
      if (withVisualViewport) {
        viewportOptions.visualViewport = makeVisualViewport({
          offsetTop: rint(rng, 0, 400),
          offsetLeft: rint(rng, 0, 400),
          width: Math.max(200, Math.floor(viewportWidth / 2)),
          height: Math.max(200, Math.floor(viewportHeight / 2)),
        });
      }

      document.body.innerHTML = '<div id="fa"></div><div id="ft"></div>';
      const a = document.getElementById('fa');
      const t = document.getElementById('ft');
      mockRect(a, {top: anchorTop, left: anchorLeft, width: anchorWidth, height: anchorHeight});
      mockRect(t, {top: 0, left: 0, width: targetWidth, height: targetHeight});

      const ab = position(t, a, dropdownPositionStrategy, undefined, makeViewport(viewportOptions));

      const effectiveTop = parsePx(t.style.getPropertyValue('--target-top'));
      const effectiveLeft = parsePx(t.style.getPropertyValue('--target-left'));
      ab();

      return {
        input: {
          ...viewportOptions,
          anchorWidth,
          anchorHeight,
          anchorTop,
          anchorLeft,
          targetWidth,
          targetHeight,
        },
        effectiveTop,
        effectiveLeft,
      };
    }

    function adjacency({input, effectiveTop, effectiveLeft}) {
      const {anchorTop, anchorLeft, anchorWidth, anchorHeight, targetHeight, targetWidth} = input;
      const tol = 0.5;
      const expectedBelow = anchorTop + anchorHeight;
      const expectedAbove = anchorTop - targetHeight;
      const expectedFlushLeft = anchorLeft;
      const expectedFlushRight = anchorLeft + anchorWidth - targetWidth;
      return {
        vertical:
          Math.abs(effectiveTop - expectedBelow) < tol ||
          Math.abs(effectiveTop - expectedAbove) < tol,
        horizontal:
          Math.abs(effectiveLeft - expectedFlushLeft) < tol ||
          Math.abs(effectiveLeft - expectedFlushRight) < tol,
      };
    }

    it('always keeps the dropdown adjacent to its anchor (no visualViewport)', () => {
      const N = 2000;
      const failures = [];
      for (let i = 0; i < N; i++) {
        const result = runScenario(makeRng(0xc0ffee00 + i));
        const adj = adjacency(result);
        if (!adj.vertical || !adj.horizontal) {
          failures.push({seed: 0xc0ffee00 + i, ...result, ...adj});
        }
      }
      if (failures.length) {
        // eslint-disable-next-line no-console
        console.log(
          `Failures: ${failures.length}/${N}.`,
          JSON.stringify(failures.slice(0, 3), null, 2)
        );
      }
      expect(failures).toHaveLength(0);
    });

    it('always keeps the dropdown adjacent to its anchor (with visualViewport)', () => {
      // Same fuzz with a visualViewport simulating pinch-zoom-and-pan or
      // keyboard. Adjacency in layout coords must still hold.
      const N = 2000;
      const failures = [];
      for (let i = 0; i < N; i++) {
        const result = runScenario(makeRng(0xbadcafe0 + i), true);
        const adj = adjacency(result);
        if (!adj.vertical || !adj.horizontal) {
          failures.push({seed: 0xbadcafe0 + i, ...result, ...adj});
        }
      }
      if (failures.length) {
        // eslint-disable-next-line no-console
        console.log(
          `Failures: ${failures.length}/${N}.`,
          JSON.stringify(failures.slice(0, 3), null, 2)
        );
      }
      expect(failures).toHaveLength(0);
    });
  });

  describe('dropdownPositionStrategy — visual viewport offsets', () => {
    // These tests exercise the visualViewport.offsetTop/Left compensation in
    // getGeometry/setTop/setLeft. The offsets are non-zero when the user has
    // pinch-zoomed and panned: the visual viewport sits inside (offset from)
    // the layout viewport.

    it('does not detach the dropdown when the user is pinch-zoomed and panned', () => {
      // Mirrors the production bug report: a non-responsive form on mobile,
      // user pinch-zooms in to read it, dropdown opens — must stay glued to
      // the anchor visually.
      //
      // Layout viewport: full phone width. User has zoomed in (so the visible
      // visual viewport is smaller) and panned ~500px down. The anchor is in
      // their currently-visible area.
      mockRect(anchor, {top: 620, left: 20, width: 350, height: 40});
      mockRect(target, {top: 0, left: 0, width: 350, height: 120});

      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({
          width: 400,
          height: 1280,
          visualViewport: makeVisualViewport({offsetTop: 500, width: 400, height: 600}),
        })
      );

      // anchorBottom = anchorRect.bottom = 660 (layout coords, no offsetTop
      // added). setTop(660) → --target-top: 660px. For position:fixed,
      // `top` is interpreted in layout-viewport coords too, so the dropdown
      // renders at layout-y=660. Visually that's visual-y = 660 - 500 = 160,
      // right under the anchor (which is visually at 120–160). No gap.
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(660);
    });

    it('does not add visualViewport.offsetTop to anchor coordinates', () => {
      mockRect(anchor, {top: 100, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({
          // User has panned 50px down inside a zoomed view.
          visualViewport: makeVisualViewport({offsetTop: 50}),
        })
      );

      // anchorBottom = anchorRect.bottom = 130 (no offsetTop addition).
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(130);
    });

    it('registers visualViewport resize/scroll listeners when visualViewport is provided', () => {
      mockRect(anchor, {top: 100, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      const visualViewport = makeVisualViewport();
      abort = position(
        target,
        anchor,
        dropdownPositionStrategy,
        undefined,
        makeViewport({visualViewport})
      );

      const eventNames = visualViewport.addEventListener.mock.calls.map(([name]) => name);
      expect(eventNames).toEqual(expect.arrayContaining(['resize', 'scroll']));
    });

    it('does not blow up when visualViewport is null (no visual viewport)', () => {
      mockRect(anchor, {top: 100, left: 50, width: 200, height: 30});
      mockRect(target, {top: 0, left: 0, width: 200, height: 200});

      expect(() => {
        abort = position(
          target,
          anchor,
          dropdownPositionStrategy,
          undefined,
          makeViewport({visualViewport: null})
        );
      }).not.toThrow();

      // anchorBottom = 130 (no offset added)
      expect(parsePx(target.style.getPropertyValue('--target-top'))).toBe(130);
    });
  });
});
