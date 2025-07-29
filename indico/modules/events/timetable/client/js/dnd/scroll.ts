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
const SCROLL_MAX_OFFSET_PX = 100;
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

      // const rect = scrollParent.getBoundingClientRect();
      // const dragRect = draggable.node.current.getBoundingClientRect();

      // const draggablePosTop = dragRect.top - rect.top + scrollParent.scrollTop;
      // const draggablePosBottom = draggablePosTop + dragRect.height;

      scrollSpeed.current = getScrollSpeed({x: event.clientX, y: event.clientY}, scrollParent);

      // console.log('top', draggablePosTop, 'rrr', Math.random());
      // console.log(limits);
      // if (
      //   draggablePosTop <= limits[0] + BASE_SPEED ||
      //   draggablePosBottom >= limits[1] - BASE_SPEED
      // ) {
      //   console.log('no speed here');
      //   scrollSpeed.current.y = 0;
      // }

      if (scrollSpeed.current.x !== 0 || scrollSpeed.current.y !== 0) {
        if (intervalRef.current === null) {
          intervalRef.current = setInterval(() => {
            const parentRect = scrollParent.getBoundingClientRect();
            const dragRect = draggable.node.current.getBoundingClientRect();

            const draggableTop = dragRect.top - parentRect.top + scrollParent.scrollTop;
            const draggableBottom = draggableTop + dragRect.height;

            // const newTop = draggableTop + scrollSpeed.current.y;
            const newTop = scrollSpeed.current.y + scrollParent.scrollTop;
            const newBottom = draggableBottom + scrollSpeed.current.y;

            if (newTop + SCROLL_MAX_OFFSET_PX <= limits[0]) {
              scrollSpeed.current.y = 0;
            } else if (newBottom - SCROLL_MAX_OFFSET_PX >= limits[1]) {
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
  }, [state, draggables, enabled]);
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
