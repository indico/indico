// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
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

const verticalPreferAbovePosition = {
  calculateFit() {
    const targetRect = this.target.getBoundingClientRect();
    const anchorRect = this.anchor.getBoundingClientRect();
    this.fitsPreferredDirection = targetRect.height <= anchorRect.top;
  },
  setPosition() {
    this.target.style.setProperty('--target-top', this.fitsPreferredDirection ? 'auto' : '100%');
    this.target.style.setProperty('--target-bottom', this.fitsPreferredDirection ? '100%' : 'auto');
  },
};

const verticalPreferBelowPosition = {
  calculateFit() {
    const targetRect = this.target.getBoundingClientRect();
    const anchorRect = this.anchor.getBoundingClientRect();
    this.fitsPreferredDirection = anchorRect.bottom + targetRect.height <= viewportHeight;
  },
  setPosition() {
    this.target.style.setProperty('--target-top', this.fitsPreferredDirection ? '100%' : 'auto');
    this.target.style.setProperty('--target-bottom', this.fitsPreferredDirection ? 'auto' : '100%');
  },
};

const unaligned = {
  calculateAlignment() {},
  setAlignment() {},
};

const horizontalFlush = {
  calculateAlignment() {
    const targetRect = this.target.getBoundingClientRect();
    const anchorRect = this.anchor.getBoundingClientRect();
    this.alignsPreferredSide = anchorRect.left + targetRect.width <= viewportWidth;
  },
  setAlignment() {
    this.target.style.setProperty('--target-left', this.alignsPreferredSide ? '0' : 'auto');
    this.target.style.setProperty('--target-right', this.alignsPreferredSide ? 'auto' : '0');
  },
};

const horizontalTargetPosition = {
  calculateFit() {
    const targetRect = this.target.getBoundingClientRect();
    const anchorRect = this.anchor.getBoundingClientRect();
    this.fitsPreferredDirection = targetRect.width <= viewportWidth - anchorRect.right;
  },
  setPosition() {
    this.target.style.setProperty('--target-left', this.fitsPreferredDirection ? '100%' : 'auto');
    this.target.style.setProperty('--target-right', this.fitsPreferredDirection ? 'auto' : '100%');
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
  ...verticalPreferAbovePosition,
  ...unaligned,
  ...withArrow,
  ...verticalArrowPosition,
};

export const horizontalTooltipPositionStrategy = {
  ...horizontalTargetPosition,
  ...unaligned,
  ...withArrow,
  ...horizontalArrowPosition,
};

export const dropdownPositionStrategy = {
  ...verticalPreferBelowPosition,
  ...horizontalFlush,
  ...withoutArrow,
};

export const popupPositionStrategy = {
  ...verticalPreferAbovePosition,
  ...unaligned,
  ...withoutArrow,
};

/**
 * Calculate whether the target element will fit the space below the anchor and apply position styling
 */
export function position(target, anchor, strategy, callback) {
  strategy = Object.create(strategy);
  strategy.target = target;
  strategy.anchor = anchor;

  // Since hidden elements will not have a client rect, we need to first simulate
  // the open state and wait for a reflow. This is done by applying the position
  // preview marker attribute to the target element. It is recommended to visually
  // hide the element while the preview attribute is preset (e.g., opacity: 0) since
  // we are only interested in the client rect and not its other visual properties.
  target.toggleAttribute('data-position-check', true);

  requestAnimationFrame(() => {
    strategy.calculateFit();
    strategy.calculateAlignment();
    target.removeAttribute('data-position-check');
    strategy.setPosition();
    strategy.setAlignment();
    strategy.setArrowDirection();
    callback?.(strategy.fitsPreferredDirection);
  });
}
