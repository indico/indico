// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {MouseEvent as SyntheticMouseEvent} from 'react';

import {MIN_DURATION, minutesToPixels, pixelsToMinutes} from './utils';

import './DayTimetable.module.scss';

const gridSize = minutesToPixels(5);

export default function ResizeHandle({
  duration,
  minDuration = MIN_DURATION,
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
    const handlers = new Map<keyof DocumentEventMap, (event: unknown) => void>();

    function addEventListener<K extends keyof DocumentEventMap>(
      type: K,
      handler: (event: DocumentEventMap[K]) => void
    ) {
      handlers.set(type, handler);
      document.addEventListener(type, handler);
    }

    function removeEventListeners() {
      for (const [type, handler] of handlers.entries()) {
        document.removeEventListener(type, handler);
      }
    }

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
      removeEventListeners();

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

    const keyDownHandler = (keyDownEvent: KeyboardEvent) => {
      if (keyDownEvent.key !== 'Escape') {
        return;
      }

      removeEventListeners();

      if (resizeStartRef.current === null) {
        return;
      }
      setIsResizing(false);
      setLocalDuration(duration);
    };

    addEventListener('mousemove', mouseMoveHandler);
    addEventListener('mouseup', mouseUpHandler);
    addEventListener('keydown', keyDownHandler);
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
