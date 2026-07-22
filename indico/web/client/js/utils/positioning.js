// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Positioning strategies
//
// The mixins represent the generic positioning methods, while the
// scenario-specific positioning methods are defined using the mixins.
// You will notice that mixins are not exported, while scenario-specific
// positioning strategies are exported.
//
// The exported strategies are used by the position() function further
// below.
//
// The code in this module is used in conjunction with the CSS. It relies
// on the following behavior:
//
// The dropdown / popup targets are positioned using `position: fixed`,
// whose `top`/`left` resolve against the *layout* viewport. The geometry
// reads (`getBoundingClientRect`, `window.scrollY/X`) are in the same
// frame, so we do not need — and must not apply — any visual-viewport
// compensation: doing so would double-shift the target by
// `visualViewport.offsetTop`/`offsetLeft` whenever the user is
// pinch-zoomed and panned (a common case on non-responsive pages
// viewed on mobile).
//
// We do still listen for `visualViewport`'s resize/scroll events so
// the position is recomputed when the visible area changes (virtual
// keyboard, zoom in/out), but the offsets themselves are not folded
// into the coordinates.
//
// Note that the calculations do not account for elastic scroll.

// `position: fixed` resolves `top`/`left` against the layout viewport — UNLESS an
// ancestor establishes a containing block for fixed descendants (a `transform`,
// `filter`, `perspective`, a `will-change` naming one of those, or paint/layout
// containment). When that happens — e.g. a tooltip rendered inside a Popper-
// positioned popup, which is placed with a transform — the target's `top`/`left`
// are measured from that ancestor's padding box instead of the viewport, so the
// viewport coordinates the strategies compute land in the wrong place. We shift
// them back by the ancestor's position. With no such ancestor (every normal
// tooltip/dropdown) the offset is zero and behavior is unchanged.
//
// This compensates for the ancestor's translation, which covers the real cases
// (popups, dropdowns, animated containers). A scaled or rotated container would
// need full transform-matrix inversion, which we don't attempt here.
function getFixedContainingBlockOffset(target) {
  for (let node = target.parentElement; node; node = node.parentElement) {
    const styles = getComputedStyle(node);
    const establishesContainingBlock =
      styles.transform !== 'none' ||
      styles.perspective !== 'none' ||
      (styles.filter !== undefined && styles.filter !== 'none') ||
      styles.willChange
        .split(',')
        .some(p => ['transform', 'perspective', 'filter'].includes(p.trim())) ||
      /\b(paint|layout|strict|content)\b/.test(styles.contain);
    if (establishesContainingBlock) {
      const rect = node.getBoundingClientRect();
      // The containing block for fixed/absolute is the padding box, so step in
      // past the border.
      return {top: rect.top + node.clientTop, left: rect.left + node.clientLeft};
    }
  }
  return {top: 0, left: 0};
}

const geometry = {
  setAnchorGeometry() {
    this.anchorRect ??= this.anchor.getBoundingClientRect();
    this.anchorWidth ??= this.anchorRect.width;
    this.anchorHeight ??= this.anchorRect.height;
    // Set anchor geometry information on the target for targets
    // that need to match the anchor dimensions (e.g., dropdowns)
    this.target.style.setProperty('--anchor-width', `${this.anchorWidth}px`);
    this.target.style.setProperty('--anchor-height', `${this.anchorHeight}px`);
  },
  getGeometry() {
    this.targetRect ??= this.target.getBoundingClientRect();
    this.anchorRect ??= this.anchor.getBoundingClientRect();
    // Vertical geometry
    this.targetHeight ??= this.targetRect.height;
    this.anchorHeight ??= this.anchorRect.height;
    this.anchorTop ??= this.getVisualY(this.anchorRect.top);
    this.anchorBottom ??= this.getVisualY(this.anchorRect.bottom);
    // Horizontal geometry
    this.targetWidth ??= this.targetRect.width;
    this.anchorWidth ??= this.anchorRect.width;
    this.anchorLeft ??= this.getVisualX(this.anchorRect.left);
    this.anchorRight ??= this.getVisualX(this.anchorRect.right);
    // Initial scroll positions
    // XXX: These are remembered because, instead of calculating the
    // positions of each element over and over for each scroll event,
    // we simply adjust the position based on scroll distance. This
    // prevents layout thrashing because scroll positions can be read
    // without forced reflow.
    this.initialScrollTop = this.getScrollTop();
    this.initialScrollLeft = this.getScrollLeft();
    // Offset of the target's fixed containing block (zero unless a transformed
    // ancestor is in play); see getFixedContainingBlockOffset.
    this.containingBlockOffset ??= getFixedContainingBlockOffset(this.target);
  },
  resetGeometry(callback) {
    delete this.anchorRect;
    delete this.anchorWidth;
    delete this.anchorHeight;
    delete this.anchorTop;
    delete this.anchorBottom;
    delete this.anchorLeft;
    delete this.anchorRight;
    delete this.targetRect;
    delete this.targetWidth;
    delete this.targetHeight;
    delete this.initialScrollTop;
    delete this.initialScrollLeft;
    delete this.containingBlockOffset;

    this.setAnchorGeometry();
    requestAnimationFrame(() => {
      this.getGeometry();
      callback();
    });
  },
  setTop(top) {
    const scrollOffset = this.getScrollTop() - this.initialScrollTop;
    this.target.style.setProperty(
      '--target-top',
      `${top - scrollOffset - this.containingBlockOffset.top}px`
    );
  },
  setLeft(left) {
    const scrollOffset = this.getScrollLeft() - this.initialScrollLeft;
    this.target.style.setProperty(
      '--target-left',
      `${left - scrollOffset - this.containingBlockOffset.left}px`
    );
  },
};

const verticalPreferAbovePosition = {
  calculateFit() {
    const roomAbove = this.anchorTop - this.visibleTop;
    const roomBelow = this.visibleBottom - this.anchorBottom;
    const fitsAbove = this.targetHeight <= roomAbove;
    const fitsBelow = this.targetHeight <= roomBelow;
    this.fitsPreferredDirection = fitsAbove || (!fitsBelow && roomAbove >= roomBelow);
  },
  setPosition() {
    if (this.fitsPreferredDirection) {
      this.setTop(this.anchorTop - this.targetHeight);
    } else {
      this.setTop(this.anchorBottom);
    }
  },
};

const verticalPreferBelowPosition = {
  calculateFit() {
    const roomBelow = this.visibleBottom - this.anchorBottom;
    const roomAbove = this.anchorTop - this.visibleTop;
    const fitsBelow = this.targetHeight <= roomBelow;
    const fitsAbove = this.targetHeight <= roomAbove;
    this.fitsPreferredDirection = fitsBelow || (!fitsAbove && roomBelow >= roomAbove);
  },
  setPosition() {
    if (this.fitsPreferredDirection) {
      this.setTop(this.anchorBottom);
    } else {
      this.setTop(this.anchorTop - this.targetHeight);
    }
  },
};

const unaligned = {
  calculateAlignment() {},
  setAlignment() {},
};

const verticalCenter = {
  calculateAlignment() {},
  setAlignment() {
    this.setTop(this.anchorTop + (this.anchorHeight - this.targetHeight) / 2);
  },
};

const horizontalCenter = {
  calculateAlignment() {},
  setAlignment() {
    this.setLeft(this.anchorLeft + (this.anchorWidth - this.targetWidth) / 2);
  },
};

const horizontalFlush = {
  calculateAlignment() {
    const spaceForFlushLeft = this.visibleRight - this.anchorLeft;
    const spaceForFlushRight = this.anchorRight - this.visibleLeft;
    const flushLeftFits = this.targetWidth <= spaceForFlushLeft;
    const flushRightFits = this.targetWidth <= spaceForFlushRight;
    this.alignsPreferredSide =
      flushLeftFits || (!flushRightFits && spaceForFlushLeft >= spaceForFlushRight);
  },
  setAlignment() {
    if (this.alignsPreferredSide) {
      this.setLeft(this.anchorLeft);
    } else {
      this.setLeft(this.anchorRight - this.targetWidth);
    }
  },
};

const horizontalTargetPosition = {
  calculateFit() {
    const roomRight = this.visibleRight - this.anchorRight;
    const roomLeft = this.anchorLeft - this.visibleLeft;
    const fitsRight = this.targetWidth <= roomRight;
    const fitsLeft = this.targetWidth <= roomLeft;
    this.fitsPreferredDirection = fitsRight || (!fitsLeft && roomRight >= roomLeft);
  },
  setPosition() {
    if (this.fitsPreferredDirection) {
      this.setLeft(this.anchorRight);
    } else {
      this.setLeft(this.anchorLeft - this.targetWidth);
    }
  },
};

const withArrow = {
  setArrowDirection() {
    if (this.fitsPreferredDirection) {
      this.setPreferredArrowDirection();
    } else {
      this.setOppositeArrowDirection();
    }
  },
};

const withoutArrow = {
  setArrowDirection() {},
};

const verticalArrowPosition = {
  setPreferredArrowDirection() {
    const style = this.anchor.style;
    style.setProperty('--arrow-top', 'auto');
    style.setProperty('--arrow-direction', '180deg');
  },
  setOppositeArrowDirection() {
    const style = this.anchor.style;
    style.setProperty('--arrow-top', '100%');
    style.setProperty('--arrow-direction', '0');
  },
};

const horizontalArrowPosition = {
  setPreferredArrowDirection() {
    const style = this.anchor.style;
    style.setProperty('--arrow-left', '100%');
    style.setProperty('--arrow-direction', '-90deg');
  },
  setOppositeArrowDirection() {
    const style = this.anchor.style;
    style.setProperty('--arrow-left', 'auto');
    style.setProperty('--arrow-direction', '90deg');
  },
};

export const verticalTooltipPositionStrategy = {
  ...geometry,
  ...verticalPreferAbovePosition,
  ...horizontalCenter,
  ...withArrow,
  ...verticalArrowPosition,
};

export const horizontalTooltipPositionStrategy = {
  ...geometry,
  ...horizontalTargetPosition,
  ...verticalCenter,
  ...withArrow,
  ...horizontalArrowPosition,
};

export const dropdownPositionStrategy = {
  ...geometry,
  ...verticalPreferBelowPosition,
  ...horizontalFlush,
  ...withoutArrow,
};

export const popupPositionStrategy = {
  ...geometry,
  ...verticalPreferAbovePosition,
  ...unaligned,
  ...withoutArrow,
};

/**
 * Calculate whether the target element will fit the space around the
 * anchor and apply position styling to clear the anchor.
 *
 * The exact strategy for calculating these values is defined by the
 * `*Strategy` objects defined in this module.
 *
 * The fifth argument allows the caller to override the viewport
 * accessors used by the strategies. The defaults read from the live
 * `window` / `document.documentElement` / `window.visualViewport`,
 * which is what production code wants. Tests can pass in fakes to
 * exercise specific viewport scenarios without monkey-patching
 * globals.
 */
export function position(
  target,
  anchor,
  strategy,
  callback,
  {
    visualViewport = typeof window !== 'undefined' ? window.visualViewport : null,
    documentElement = typeof document !== 'undefined' ? document.documentElement : null,
    windowObj = typeof window !== 'undefined' ? window : null,
  } = {}
) {
  strategy = Object.create(strategy);
  strategy.target = target;
  strategy.anchor = anchor;

  // Per-call viewport accessors. Defined as getters so the strategies
  // see the current size on each access (the viewport can change
  // mid-positioning due to scrollbar appearance, address-bar collapse,
  // virtual keyboard show/hide, pinch-zoom pan, etc.).
  //
  // `viewportWidth`/`viewportHeight` are the LAYOUT viewport — the
  // coordinate space `getBoundingClientRect` and `position: fixed` use.
  // `visibleTop`/`visibleBottom`/`visibleLeft`/`visibleRight` are the
  // edges of the currently-VISIBLE area expressed in the same layout
  // coordinates. When there is a visual viewport (mobile, pinch-zoom,
  // keyboard), the visible area is a window inside the layout viewport;
  // when there is none, the two coincide. Strategies use the visible-area
  // accessors when deciding whether the target fits on a given side.
  Object.defineProperty(strategy, 'viewportWidth', {
    get: () => documentElement.clientWidth,
  });
  Object.defineProperty(strategy, 'viewportHeight', {
    get: () => documentElement.clientHeight,
  });
  Object.defineProperty(strategy, 'visibleTop', {
    get: () => visualViewport?.offsetTop ?? 0,
  });
  Object.defineProperty(strategy, 'visibleBottom', {
    get: () =>
      (visualViewport?.offsetTop ?? 0) + (visualViewport?.height ?? documentElement.clientHeight),
  });
  Object.defineProperty(strategy, 'visibleLeft', {
    get: () => visualViewport?.offsetLeft ?? 0,
  });
  Object.defineProperty(strategy, 'visibleRight', {
    get: () =>
      (visualViewport?.offsetLeft ?? 0) + (visualViewport?.width ?? documentElement.clientWidth),
  });
  strategy.getScrollTop = () => windowObj.scrollY;
  strategy.getScrollLeft = () => windowObj.scrollX;
  strategy.getVisualY = y => y;
  strategy.getVisualX = x => x;

  const positioningAbortController = new AbortController();
  const adjustPosition = () => {
    strategy.setPosition();
    strategy.setAlignment();
    strategy.setArrowDirection();
  };
  const adjustWithFullGeometryReset = () => strategy.resetGeometry(adjustPosition);

  windowObj.addEventListener('resize', adjustWithFullGeometryReset, {
    signal: positioningAbortController.signal,
  });
  windowObj.addEventListener('scroll', adjustPosition, {
    signal: positioningAbortController.signal,
    passive: true,
  });
  visualViewport?.addEventListener('resize', adjustWithFullGeometryReset, {
    signal: positioningAbortController.signal,
  });
  // XXX: This is not a standard scroll event. It only fires *once* after the
  // scroll is finished.
  visualViewport?.addEventListener('scroll', adjustWithFullGeometryReset, {
    signal: positioningAbortController.signal,
  });

  // Since hidden elements will not have a client rect, we need to first simulate
  // the open state and wait for a reflow. This is done by applying the position
  // preview marker attribute to the target element. It is recommended to visually
  // hide the element while the preview attribute is preset (e.g., opacity: 0) since
  // we are only interested in the client rect and not its other visual properties.
  target.toggleAttribute('data-position-check', true);

  strategy.resetGeometry(() => {
    strategy.calculateFit();
    strategy.calculateAlignment();
    target.removeAttribute('data-position-check');
    adjustPosition();
    requestAnimationFrame(() => {
      callback?.(strategy.fitsPreferredDirection);
    });
  });

  return () => positioningAbortController.abort();
}
