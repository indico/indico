// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

const DEFAULT_POSITION_OPTIONS = {
  // Attribute used to simulate the expanded state so that position can be calculated
  positionPreviewMarkerAttribute: 'data-position-check',
  // Target bottom style setter
  setStyle(target, targetWillFitBelow) {
    target.style.setProperty('--target-bottom', targetWillFitBelow ? 'auto' : '100%');
  },
  // Function to reveal the target once position styles are applied
  // eslint-disable-next-line no-unused-vars
  expand(target, anchor) {
    throw Error('expand() option is required');
  },
};

/**
 * Calculate whether the target element will fit the space below the anchor and apply position styling
 */
export function topBottomPosition(target, anchor, options = {}) {
  options = {...DEFAULT_POSITION_OPTIONS, ...options};

  // Since hidden elements will not have a client rect, we need to first simulate
  // the open state and wait for a reflow. This is done by applying the position
  // preview marker attribute to the target element. It is recommended to visually
  // hide the element while the preview attribute is preset (e.g., opacity: 0) since
  // we are only interested in the client rect and not its other visual properties.
  target.toggleAttribute(options.positionPreviewMarkerAttribute, true);

  requestAnimationFrame(() => {
    const anchorRect = anchor.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const targetBottom = anchorRect.bottom + targetRect.height;
    const targetWillFitBelow = targetBottom < window.innerHeight;
    target.removeAttribute(options.positionPreviewMarkerAttribute);
    options.setStyle(target, targetWillFitBelow);
    options.expand(target, anchor);
  });
}
