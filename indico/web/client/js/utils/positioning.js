// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';

let viewportWidth = document.documentElement.clientWidth;
let viewportHeight = document.documentElement.clientHeight;

function matrixMultiply(m1, m2) {
  if (!m1) {
    return m2;
  }
  if (!m2) {
    return m1;
  }

  return {
    a: m1.a * m2.a + m1.c * m2.b,
    b: m1.b * m2.a + m1.d * m2.b,
    c: m1.a * m2.c + m1.c * m2.d,
    d: m1.b * m2.c + m1.d * m2.d,
    e: m1.a * m2.e + m1.c * m2.f + m1.e,
    f: m1.b * m2.e + m1.d * m2.f + m1.f,
  };
}

function parseMatrix(transformString) {
  if (!transformString || transformString === 'none') {
    return null;
  }

  const match = transformString.match(/matrix\(([^)]+)\)/);
  if (match) {
    const values = match[1].split(',').map(v => parseFloat(v.trim()));
    return {
      a: values[0],
      b: values[1],
      c: values[2],
      d: values[3],
      e: values[4],
      f: values[5],
    };
  }

  const match3d = transformString.match(/matrix3d\(([^)]+)\)/);
  if (match3d) {
    const values = match3d[1].split(',').map(v => parseFloat(v.trim()));
    return {
      a: values[0],
      b: values[1],
      c: values[4],
      d: values[5],
      e: values[12],
      f: values[13],
    };
  }

  return null;
}

const transformCache = new WeakMap();

function getCumulativeTransform(element) {
  if (transformCache.has(element)) {
    return transformCache.get(element);
  }

  const transforms = [];
  let current = element;

  while (current && current !== document.documentElement) {
    const style = window.getComputedStyle(current);
    const matrix = parseMatrix(style.transform);
    if (matrix) {
      transforms.push(matrix);
    }
    current = current.parentElement;
  }

  let cumulative = null;
  for (let i = transforms.length - 1; i >= 0; i--) {
    cumulative = matrixMultiply(cumulative, transforms[i]);
  }

  transformCache.set(element, cumulative);
  return cumulative;
}

domReady.then(() => setTimeout(updateClientGeometry));
window.addEventListener('resize', updateClientGeometry);

function updateClientGeometry() {
  viewportWidth = document.documentElement.clientWidth;
  viewportHeight = document.documentElement.clientHeight;
}

// XXX: On Safari (and generally browsers that support visual viewports)
// we use calculations based around the visual viewport offsets to account
// for the UI overlays such as virtual keyboards. For efficiency, the following
// functions have dual definitions based on whether the visual viewport is
// supported, so that we don't test for it on every call.
//
// Visual viewport offsets determine how much the viewport is pushed uo (or
// left) compared to its original location when the UI overlay is not shown.
// Therefore we must *add* these offsets to compensate.
//
// Note that currently these calculations do not account for elastic scroll.
// You should expect that the calculations are going to be off by some margin
// while the elastic scroll is in effect. There is no known (to me) method that
// accounts for these. If you find it, you should apply it to these functions,
// as they represent the single source of truth for any kind of coordinate
// adjustment.

const hasVisualViewport = window.visualViewport !== undefined;

const getScrollTop = hasVisualViewport
  ? () => window.scrollY + visualViewport.offsetTop
  : () => window.scrollY;

const getScrollLeft = hasVisualViewport
  ? () => window.scrollX + visualViewport.offsetLeft
  : () => window.scrollX;

const getVisualY = hasVisualViewport ? y => y + visualViewport.offsetTop : y => y;

const getVisualX = hasVisualViewport ? x => x + visualViewport.offsetLeft : x => x;

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

    // Horizontal geometry
    this.targetWidth ??= this.targetRect.width;
    this.anchorWidth ??= this.anchorRect.width;

    // Check for transformed ancestors and use appropriate strategy
    const anchorTransform = getCumulativeTransform(this.anchor);

    if (anchorTransform) {
      this.getGeometryInTransformed();
    } else {
      this.getGeometryInViewport();
    }

    // Initial scroll positions
    // XXX: These are remembered because, instead of calculating the
    // positions of each element over and over for each scroll event,
    // we simply adjust the position based on scroll distance. This
    // prevents layout thrashing because scroll positions can be read
    // without forced reflow.
    this.initialScrollTop = getScrollTop();
    this.initialScrollLeft = getScrollLeft();
  },

  getGeometryInViewport() {
    // Original viewport-based positioning
    this.anchorTop ??= getVisualY(this.anchorRect.top);
    this.anchorBottom ??= getVisualY(this.anchorRect.bottom);
    this.anchorLeft ??= getVisualX(this.anchorRect.left);
    this.anchorRight ??= getVisualX(this.anchorRect.right);

    // Calculate viewport bounds for clamping
    this.clampTop = 0;
    this.clampBottom = viewportHeight - this.targetHeight;
    this.clampLeft = 0;
    this.clampRight = viewportWidth - this.targetWidth;

    // For fit calculations, use viewport dimensions
    this.availableSpaceBelow = viewportHeight - this.anchorBottom;
    this.availableSpaceAbove = this.anchorTop;
    this.availableSpaceRight = viewportWidth - this.anchorRight;
    this.availableSpaceLeft = this.anchorLeft;
  },

  getGeometryInTransformed() {
    // Find the closest transformed ancestor
    let transformedContainer = this.anchor.parentElement;
    while (transformedContainer && transformedContainer !== document.documentElement) {
      const style = window.getComputedStyle(transformedContainer);
      if (style.transform && style.transform !== 'none') {
        break;
      }
      transformedContainer = transformedContainer.parentElement;
    }

    if (transformedContainer) {
      // Calculate actual offset between container and anchor
      const containerRect = transformedContainer.getBoundingClientRect();

      // This gives us the real offset including margins, padding, etc.
      const actualOffsetTop = this.anchorRect.top - containerRect.top;
      const actualOffsetBottom = this.anchorRect.bottom - containerRect.top;
      const actualOffsetLeft = this.anchorRect.left - containerRect.left;
      const actualOffsetRight = this.anchorRect.right - containerRect.left;

      this.anchorTop ??= getVisualY(actualOffsetTop);
      this.anchorBottom ??= getVisualY(actualOffsetBottom);
      this.anchorLeft ??= getVisualX(actualOffsetLeft);
      this.anchorRight ??= getVisualX(actualOffsetRight);

      // Calculate viewport-relative bounds for clamping
      // We need to keep the dropdown within the actual viewport, not the container
      const containerViewportTop = containerRect.top;
      const containerViewportLeft = containerRect.left;

      // Calculate available space from current position to viewport edges
      // For the top clamp: we can go negative (above container) if there's viewport space above
      this.clampTop = -containerViewportTop;
      this.clampBottom = viewportHeight - containerViewportTop - this.targetHeight;
      this.clampLeft = -containerViewportLeft;
      this.clampRight = viewportWidth - containerViewportLeft - this.targetWidth;

      // For fit calculations, calculate actual available viewport space
      // Convert container-relative positions back to viewport coordinates for fit calculations
      const anchorViewportTop = containerViewportTop + actualOffsetTop;
      const anchorViewportBottom = containerViewportTop + actualOffsetBottom;
      const anchorViewportLeft = containerViewportLeft + actualOffsetLeft;
      const anchorViewportRight = containerViewportLeft + actualOffsetRight;

      this.availableSpaceBelow = viewportHeight - anchorViewportBottom;
      this.availableSpaceAbove = anchorViewportTop;
      this.availableSpaceRight = viewportWidth - anchorViewportRight;
      this.availableSpaceLeft = anchorViewportLeft;
    } else {
      // Fallback to viewport strategy
      this.getGeometryInViewport();
    }
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
    delete this.clampTop;
    delete this.clampBottom;
    delete this.clampLeft;
    delete this.clampRight;
    delete this.availableSpaceBelow;
    delete this.availableSpaceAbove;
    delete this.availableSpaceRight;
    delete this.availableSpaceLeft;

    transformCache.delete(this.anchor);
    transformCache.delete(this.target);
    this.setAnchorGeometry();
    requestAnimationFrame(() => {
      this.getGeometry();
      callback();
    });
  },
  setTop(top) {
    const scrollOffset = getScrollTop() - this.initialScrollTop;
    this.target.style.setProperty(
      '--target-top',
      `clamp(${this.clampTop}px, ${top - scrollOffset}px, ${this.clampBottom}px)`
    );
  },
  setLeft(left) {
    const scrollOffset = getScrollLeft() - this.initialScrollLeft;
    this.target.style.setProperty(
      '--target-left',
      `clamp(${this.clampLeft}px, ${left - scrollOffset}px, ${this.clampRight}px)`
    );
  },
};

const verticalPreferAbovePosition = {
  calculateFit() {
    this.fitsPreferredDirection = this.targetHeight <= this.availableSpaceAbove;
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
    this.fitsPreferredDirection = this.targetHeight <= this.availableSpaceBelow;
    this.firsOppositeDirection = this.targetHeight <= this.availableSpaceAbove;
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
    this.alignsPreferredSide = this.targetWidth <= this.availableSpaceRight + this.anchorLeft;
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
    this.fitsPreferredDirection = this.targetWidth <= this.availableSpaceRight;
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
 */
export function position(target, anchor, strategy, callback) {
  strategy = Object.create(strategy);
  strategy.target = target;
  strategy.anchor = anchor;

  const positioningAbortController = new AbortController();
  const adjustPosition = () => {
    strategy.setPosition();
    strategy.setAlignment();
    strategy.setArrowDirection();
  };
  const adjustWithFullGeometryReset = () => strategy.resetGeometry(adjustPosition);

  window.addEventListener('resize', adjustWithFullGeometryReset, {
    signal: positioningAbortController.signal,
  });
  window.addEventListener('scroll', adjustPosition, {
    signal: positioningAbortController.signal,
    passive: true,
  });
  window.visualViewport?.addEventListener('resize', adjustWithFullGeometryReset, {
    signal: positioningAbortController.signal,
  });
  // XXX: This is not a standard scroll event. It only fires *once* after the
  // scroll is finished.
  window.visualViewport?.addEventListener('scroll', adjustWithFullGeometryReset, {
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
