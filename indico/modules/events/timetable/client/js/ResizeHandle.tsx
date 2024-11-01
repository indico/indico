import React, {MouseEvent as SyntheticMouseEvent} from 'react';

import {minutesToPixels, pixelsToMinutes} from './utils';

import './DayTimetable.module.scss';

const gridSize = minutesToPixels(5);

export default function ResizeHandle({
  forBlock = false,
  duration,
  minDuration = 10,
  maxDuration,
  resizeStartRef,
  setLocalDuration,
  setGlobalDuration,
  setIsResizing,
}: {
  forBlock: boolean;
  duration: number;
  minDuration?: number;
  maxDuration?: number;
  resizeStartRef: React.MutableRefObject<number | null>;
  setLocalDuration: (d: number) => void;
  setGlobalDuration: (d: number) => void;
  setIsResizing: (b: boolean) => void;
}) {
  function resizeHandler(e: SyntheticMouseEvent) {
    e.stopPropagation();
    resizeStartRef.current = e.clientY;
    setIsResizing(true);

    function mouseMoveHandler(e: MouseEvent) {
      if (resizeStartRef.current === null) {
        return;
      }

      let dy = e.clientY - resizeStartRef.current;
      dy = Math.ceil(dy / gridSize) * gridSize;
      const newDuration = duration + pixelsToMinutes(dy);
      if (newDuration >= 10) {
        setLocalDuration(newDuration);
      } else {
        setLocalDuration(10);
      }
    }

    const mouseUpHandler = (e: MouseEvent) => {
      document.removeEventListener('mouseup', mouseUpHandler);
      document.removeEventListener('mousemove', mouseMoveHandler);

      if (resizeStartRef.current === null) {
        return;
      }

      let dy = e.clientY - resizeStartRef.current;
      dy = Math.ceil(dy / gridSize) * gridSize;
      let newDuration = duration + pixelsToMinutes(dy);

      if (minDuration !== undefined) {
        newDuration = Math.max(newDuration, minDuration);
      }

      if (maxDuration !== undefined) {
        newDuration = Math.min(newDuration, maxDuration);
      }
      setGlobalDuration(newDuration);
      setIsResizing(false);
    };

    document.addEventListener('mousemove', mouseMoveHandler);
    document.addEventListener('mouseup', mouseUpHandler);
  }

  return (
    <div
      styleName={`resize-handle ${forBlock ? 'block' : ''}`}
      onMouseDown={resizeHandler}
      onPointerDown={e => {
        e.stopPropagation(); // prevent drag start on the parent block
      }}
      onClick={e => e.stopPropagation()} // prevent parent block becoming selected when resizing a child
    />
  );
}
