// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Rect, Transform, Modifier} from './types';

/**
 * Restrict a rect to be contained within another bounding rect. Taken from dnd-kit.
 * @param transform - the current transform of the element being dragged
 * @param rect - the rect which should be contained
 * @param boundingRect - the bounding rect of the container
 * @returns
 */
function restrictToBoundingRect(transform: Transform, rect: Rect, boundingRect: Rect): Transform {
  const value = {
    ...transform,
  };

  if (rect.top + transform.y <= boundingRect.top) {
    value.y = boundingRect.top - rect.top;
  } else if (rect.bottom + transform.y >= boundingRect.top + boundingRect.height) {
    value.y = boundingRect.top + boundingRect.height - rect.bottom;
  }

  if (rect.left + transform.x <= boundingRect.left) {
    value.x = boundingRect.left - rect.left;
  } else if (rect.right + transform.x >= boundingRect.left + boundingRect.width) {
    value.x = boundingRect.left + boundingRect.width - rect.right;
  }

  return value;
}

/**
 * Restrict the dragged node to be contained within the container element
 * @param containerRef React ref to the container element
 * @returns A new Transform object
 */
export const createRestrictToElement =
  (containerRef): Modifier =>
  ({draggingNodeRect, transform}) => {
    if (!draggingNodeRect || !containerRef.current) {
      return transform;
    }

    let rect = containerRef.current.getBoundingClientRect();
    const scroll = getTotalScroll(containerRef.current);
    rect = {
      // top: rect.top,
      // left: rect.left,
      // bottom: rect.bottom,
      // right: rect.right,
      // top: rect.top + scrollParent.scrollTop,
      // left: rect.left + scrollParent.scrollLeft,
      // bottom: rect.bottom + scrollParent.scrollTop,
      // right: rect.right + scrollParent.scrollLeft,
      top: rect.top + scroll.top,
      left: rect.left + scroll.left,
      bottom: rect.bottom + scroll.top,
      right: rect.right + scroll.left,
      width: rect.width,
      height: rect.height,
    };
    return restrictToBoundingRect(transform, draggingNodeRect, rect);
  };

export function getScrollParent(element: HTMLElement): HTMLElement {
  const overflowRegex = /(auto|scroll)/;
  let parent: HTMLElement | undefined = element;
  do {
    if (!parent.parentElement) {
      return document.body;
    }
    parent = parent.parentElement;
    const style = getComputedStyle(parent);
    if (overflowRegex.test(style.overflow + style.overflowY + style.overflowX)) {
      return parent;
    }
  } while (parent);
  return document.body;
}

export function getTotalScroll(element: HTMLElement): {top: number; left: number} {
  let top = 0;
  let left = 0;
  let parent: HTMLElement | undefined = element.parentElement;

  while (parent) {
    top += parent.scrollTop;
    left += parent.scrollLeft;
    parent = parent.parentElement;
  }

  return {top, left};
}

/**
 * Restrict the dragged node to be contained within the calendar if it's
 * already scheduled.
 * @param containerRef React ref to the container element
 * @returns A new Transform object
 */
export const createRestrictToCalendar =
  (containerRef): Modifier =>
  ({draggingNodeRect, transform, id}) => {
    if (id.startsWith('unscheduled-')) {
      // return createRestrictToElement(unscheduledRef)({draggingNodeRect, transform, id});
      return transform;
    }
    return createRestrictToElement(containerRef)({draggingNodeRect, transform, id});
  };
