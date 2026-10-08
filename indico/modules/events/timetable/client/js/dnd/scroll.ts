// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {MutableRefObject, useEffect, useRef} from 'react';

import {getScrollParent} from './modifiers';
import {DragState, Draggable, MousePosition} from './types';

const SCROLL_MARGIN_PERCENT = 0.15;
const SCROLL_INTERVAL_MS = 5;
const BASE_SPEED = 3;

type Timeout = ReturnType<typeof setInterval>;
export interface ScrollBounds {
  top?: number;
  bottom?: number;
}
interface ScrollState {
  state: DragState;
  activeDraggable: string | null;
}

export function useScrollIntent({
  state,
  draggables,
  enabled,
  bounds,
}: {
  state: MutableRefObject<ScrollState>;
  draggables: Record<string, Draggable>;
  enabled: boolean;
  bounds?: ScrollBounds;
}) {
  const scrollSpeed = useRef<{x: number; y: number}>({x: 0, y: 0});
  const intervalRef = useRef<Timeout | null>(null);

  useEffect(() => {
    const id = intervalRef.current;

    function cleanUp() {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    function handleMouseMove(event: MouseEvent) {
      if (
        !enabled ||
        state.current.state !== 'dragging' ||
        state.current.activeDraggable === null
      ) {
        cleanUp();
        return;
      }
      const draggable = draggables[state.current.activeDraggable];
      const scrollParent = getScrollParent(draggable.node.current);

      scrollSpeed.current = getScrollSpeed(
        {x: event.clientX, y: event.clientY},
        scrollParent,
        bounds
      );

      if (scrollSpeed.current.x !== 0 || scrollSpeed.current.y !== 0) {
        if (intervalRef.current === null) {
          intervalRef.current = setInterval(() => {
            const boundedSpeed = applyScrollBounds(scrollSpeed.current, scrollParent, bounds);
            scrollSpeed.current = boundedSpeed;
            if (boundedSpeed.x !== 0 || boundedSpeed.y !== 0) {
              scrollParent.scrollBy(boundedSpeed.x, boundedSpeed.y);
            } else {
              cleanUp();
            }
          }, SCROLL_INTERVAL_MS);
        }
      } else {
        cleanUp();
      }
    }
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      clearInterval(id);
    };
  }, [state, draggables, enabled, bounds]);
}

function getScrollSpeed(mouse: MousePosition, scrollParent: HTMLElement, bounds?: ScrollBounds) {
  const rect = scrollParent.getBoundingClientRect();
  const mouseYPercent = Math.min(1, Math.max(0, (mouse.y - rect.top) / rect.height));
  const mouseXPercent = Math.min(1, Math.max(0, (mouse.x - rect.left) / rect.width));

  let speedX = 0;
  let speedY = 0;

  if (mouseYPercent < SCROLL_MARGIN_PERCENT) {
    speedY = -BASE_SPEED * Math.min(1 / mouseYPercent / 10, 7);
  } else if (mouseYPercent > 1 - SCROLL_MARGIN_PERCENT) {
    speedY = BASE_SPEED * Math.min(1 / (1 - mouseYPercent) / 10, 7);
  }

  if (mouseXPercent < SCROLL_MARGIN_PERCENT) {
    speedX = -BASE_SPEED * Math.min(1 / mouseXPercent / 10, 7);
  } else if (mouseXPercent > 1 - SCROLL_MARGIN_PERCENT) {
    speedX = BASE_SPEED * Math.min(1 / (1 - mouseXPercent) / 10, 7);
  }

  return applyScrollBounds({x: speedX, y: speedY}, scrollParent, bounds);
}

function applyScrollBounds(
  speed: {x: number; y: number},
  scrollParent: HTMLElement,
  bounds?: ScrollBounds
) {
  let {y} = speed;

  if (bounds?.top !== undefined && y < 0) {
    y = Math.min(0, Math.max(y, bounds.top - scrollParent.scrollTop));
  } else if (bounds?.bottom !== undefined && y > 0) {
    const maxScrollTop = bounds.bottom - scrollParent.clientHeight;
    y = Math.max(0, Math.min(y, maxScrollTop - scrollParent.scrollTop));
  }

  return {...speed, y};
}
