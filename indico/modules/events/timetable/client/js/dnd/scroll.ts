import {useEffect, useRef} from 'react';

import {getScrollParent} from './modifiers';
import {Draggable, MousePosition} from './types';

const SCROLL_MARGIN_PERCENT = 0.15;
const BASE_SPEED = 30;

type Timeout = ReturnType<typeof setInterval>;

export function useScrollIntent({
  state,
  draggables,
}: {
  state: any;
  draggables: Record<string, Draggable>;
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
      if (state.current.state !== 'dragging' || state.current.activeDraggable === null) {
        cleanUp();
        return;
      }
      const draggable = draggables[state.current.activeDraggable];
      const scrollParent = getScrollParent(draggable.node.current);

      scrollSpeed.current = getScrollSpeed({x: event.clientX, y: event.clientY}, scrollParent);
      if (scrollSpeed.current.x !== 0 || scrollSpeed.current.y !== 0) {
        if (intervalRef.current === null) {
          intervalRef.current = setInterval(() => {
            if (scrollSpeed.current.x !== 0 || scrollSpeed.current.y !== 0) {
              scrollParent.scrollBy(scrollSpeed.current.x, scrollSpeed.current.y);
            }
          }, 50);
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
  }, [state, draggables]);
}

function getScrollSpeed(mouse: MousePosition, scrollParent: HTMLElement) {
  const rect = scrollParent.getBoundingClientRect();
  const mouseYPercent = (mouse.y - rect.top) / rect.height;
  const mouseXPercent = (mouse.x - rect.left) / rect.width;
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
