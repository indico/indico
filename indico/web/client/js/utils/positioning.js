// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';

let viewportWidth = document.documentElement.clientWidth;
let viewportHeight = document.documentElement.clientHeight;

domReady.then(() => setTimeout(updateClientGeometry));
window.addEventListener('resize', updateClientGeometry);

function updateClientGeometry() {
  viewportWidth = document.documentElement.clientWidth;
  viewportHeight = document.documentElement.clientHeight;
}

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
    this.anchorTop ??= this.anchorRect.top;
    this.anchorBottom ??= this.anchorRect.bottom;
    this.initialPageYOffset = window.pageYOffset;
    // Horizontal geometry
    this.targetWidth ??= this.targetRect.width;
    this.anchorWidth ??= this.anchorRect.width;
    this.anchorLeft ??= this.anchorRect.left;
    this.anchorRight ??= this.anchorRect.right;
    this.initialPageXOffset = window.pageXOffset;
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
    delete this.initialPageYOffset;

    this.setAnchorGeometry();
    requestAnimationFrame(() => {
      this.getGeometry();
      callback();
    });
  },
  setTop(top) {
    const scrollOffset = window.pageYOffset - this.initialPageYOffset;
    this.target.style.setProperty(
      '--target-top',
      `clamp(0.5em, ${top - scrollOffset}px, calc(100dvh - ${this.targetHeight}px - 0.5em))`
    );
  },
  setLeft(left) {
    const scrollOffset = window.pageXOffset - this.initialPageXOffset;
    this.target.style.setProperty(
      '--target-left',
      `clamp(0.5em, ${left - scrollOffset}px, calc(100% - ${this.targetWidth}px - 0.5em))`
    );
  },
};

const verticalPreferAbovePosition = {
  calculateFit() {
    this.fitsPreferredDirection = this.targetHeight <= this.anchorTop;
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
    this.fitsPreferredDirection = this.anchorBottom + this.targetHeight <= viewportHeight;
    this.firsOppositeDirection = this.anchorTop - this.targetHeight > 0;
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
    this.alignsPreferredSide = this.anchorLeft + this.targetWidth <= viewportWidth;
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
    this.fitsPreferredDirection = this.targetWidth <= viewportWidth - this.anchorRight;
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
  ...horizontalCenter,
  ...withArrow,
  ...verticalArrowPosition,
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

  window.addEventListener(
    'resize',
    () => {
      strategy.resetGeometry(adjustPosition);
    },
    {
      signal: positioningAbortController.signal,
    }
  );
  window.addEventListener('scroll', adjustPosition, {
    signal: positioningAbortController.signal,
    passive: true,
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
