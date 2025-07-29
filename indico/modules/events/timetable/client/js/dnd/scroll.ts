// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useEffect, useRef} from 'react';

import {getScrollParent} from './modifiers';
import {Draggable, MousePosition} from './types';

const SCROLL_MARGIN_PERCENT = 0.15;
const SCROLL_MAX_OFFSET_PX = 200;
const SCROLL_INTERVAL_MS = 5;
const BASE_SPEED = 3;

type Timeout = ReturnType<typeof setInterval>;

export function useScrollIntent({
  state,
  draggables,
  enabled,
  limits,
}: {
  state: any;
  draggables: Record<string, Draggable>;
  enabled: boolean;
  limits?: [number, number];
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

      // const dragRect = draggable.node.current.getBoundingClientRect();

      scrollSpeed.current = getScrollSpeed({x: event.clientX, y: event.clientY}, scrollParent);

      const direction = Math.sign(scrollSpeed.current.y);

      if (scrollSpeed.current.x !== 0 || scrollSpeed.current.y !== 0) {
        if (intervalRef.current === null) {
          intervalRef.current = setInterval(() => {
            const newTop = scrollSpeed.current.y + scrollParent.scrollTop;
            const newBottom =
              scrollSpeed.current.y + scrollParent.scrollTop + scrollParent.clientHeight;

            if (direction === -1 && newTop + SCROLL_MAX_OFFSET_PX <= limits[0]) {
              scrollSpeed.current.y = 0;
            } else if (direction === 1 && newBottom - SCROLL_MAX_OFFSET_PX >= limits[1]) {
              scrollSpeed.current.y = 0;
            }

            if (scrollSpeed.current.x !== 0 || scrollSpeed.current.y !== 0) {
              scrollParent.scrollBy(scrollSpeed.current.x, scrollSpeed.current.y);
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
  }, [state, draggables, enabled, limits]);
}

function getScrollSpeed(mouse: MousePosition, scrollParent: HTMLElement) {
  const rect = scrollParent.getBoundingClientRect();
  const mouseX = mouse.x - rect.left;
  const mouseY = mouse.y - rect.top;
  const mouseXPercent = Math.min(1, Math.max(0, mouseX / rect.width));
  const mouseYPercent = Math.min(1, Math.max(0, mouseY / rect.height));

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

  return {x: speedX, y: speedY};
}
