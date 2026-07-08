// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {MouseEvent as SyntheticMouseEvent} from 'react';

import {getScrollParent} from './dnd/modifiers';
import {DAY_SIZE, MIN_DURATION, minutesToPixels, pixelsToMinutes} from './utils';

import './DayTimetable.module.scss';

const gridSize = minutesToPixels(5);
const resizingCursorClass = 'timetable-entry-resizing';

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
  function resizeHandler(e: SyntheticMouseEvent<HTMLDivElement>) {
    if (e.button !== 0) {
      return;
    }

    e.stopPropagation();
    const scrollParent = getScrollParent(e.currentTarget);
    let currentClientY = e.clientY;
    clampScrollTop();
    resizeStartRef.current = e.clientY + scrollParent.scrollTop;
    document.body.classList.add(resizingCursorClass);
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

    function cleanUp() {
      removeEventListeners();
      scrollParent.removeEventListener('scroll', scrollHandler);
      document.body.classList.remove(resizingCursorClass);
    }

    function clampScrollTop() {
      const maxScrollTop = Math.max(0, DAY_SIZE - scrollParent.clientHeight);

      if (scrollParent.scrollTop > maxScrollTop) {
        scrollParent.scrollTop = maxScrollTop;
      }
    }

    function calculateNewDuration(clientY: number) {
      if (resizeStartRef.current === null) {
        return null;
      }

      clampScrollTop();
      let dy = clientY + scrollParent.scrollTop - resizeStartRef.current;
      dy = Math.ceil(dy / gridSize) * gridSize;
      let newDuration = duration + pixelsToMinutes(dy);

      if (maxDuration !== undefined) {
        // Prevent resizing beyond the end of the parent block
        newDuration = Math.min(newDuration, maxDuration);
      }

      return newDuration;
    }

    function updateLocalDuration(clientY: number) {
      const newDuration = calculateNewDuration(clientY);

      if (newDuration === null) {
        return;
      }

      setLocalDuration(Math.max(newDuration, minDuration));
    }

    function mouseMoveHandler(moveEvent: MouseEvent) {
      currentClientY = moveEvent.clientY;
      updateLocalDuration(currentClientY);
    }

    function scrollHandler() {
      updateLocalDuration(currentClientY);
    }

    const mouseUpHandler = (mouseUpEvent: MouseEvent) => {
      cleanUp();

      let newDuration = calculateNewDuration(mouseUpEvent.clientY);
      if (newDuration === null) {
        setIsResizing(false);
        return;
      }

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

      cleanUp();

      if (resizeStartRef.current === null) {
        return;
      }
      setIsResizing(false);
      setLocalDuration(duration);
    };

    addEventListener('mousemove', mouseMoveHandler);
    addEventListener('mouseup', mouseUpHandler);
    addEventListener('keydown', keyDownHandler);
    scrollParent.addEventListener('scroll', scrollHandler);
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
