// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {MouseEvent as SyntheticMouseEvent} from 'react';

import {minutesToPixels, pixelsToMinutes} from './utils';

import './DayTimetable.module.scss';

const gridSize = minutesToPixels(5);

export default function ResizeHandle({
  duration,
  minDuration = 10,
  maxDuration,
  resizeStartRef,
  setLocalDuration,
  setGlobalDuration,
  setIsResizing,
}: {
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

    function mouseMoveHandler(moveEvent: MouseEvent) {
      if (resizeStartRef.current === null) {
        return;
      }

      let dy = moveEvent.clientY - resizeStartRef.current;
      dy = Math.ceil(dy / gridSize) * gridSize;
      let newDuration = duration + pixelsToMinutes(dy);

      if (maxDuration !== undefined) {
        // Prevent resizing beyond the end of the parent block
        newDuration = Math.min(newDuration, maxDuration);
      }

      if (newDuration > minDuration) {
        setLocalDuration(newDuration);
      } else {
        setLocalDuration(minDuration);
      }
    }

    const mouseUpHandler = (mouseUpEvent: MouseEvent) => {
      document.removeEventListener('mouseup', mouseUpHandler);
      document.removeEventListener('mousemove', mouseMoveHandler);

      if (resizeStartRef.current === null) {
        return;
      }

      let dy = mouseUpEvent.clientY - resizeStartRef.current;
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
      styleName="resize-handle"
      onMouseDown={resizeHandler}
      onPointerDown={e => {
        e.stopPropagation(); // prevent drag start on the parent block
      }}
      onClick={e => e.stopPropagation()} // prevent parent block becoming selected when resizing a child
    />
  );
}
