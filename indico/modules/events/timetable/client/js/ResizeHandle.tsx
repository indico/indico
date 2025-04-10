// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editEntryTimeURL from 'indico-url:timetable.api_edit_entry_time';

import React, {MouseEvent as SyntheticMouseEvent} from 'react';
import {useSelector} from 'react-redux';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import * as selectors from './selectors';
import {minutesToPixels, pixelsToMinutes} from './utils';

import './DayTimetable.module.scss';

const gridSize = minutesToPixels(5);

async function updateEntryTime(
  id: number,
  eventId: number,
  startDt: moment.Moment,
  duration: number
) {
  const url = editEntryTimeURL({entry_id: id, event_id: eventId});
  const data = {
    start_dt: startDt.format('YYYY-MM-DD HH:mm:ss'),
    end_dt: startDt
      .clone()
      .add(duration, 'minutes')
      .format('YYYY-MM-DD HH:mm:ss'),
  };
  try {
    await indicoAxios.post(url, data);
  } catch (error) {
    handleAxiosError(error);
  }
}

export default function ResizeHandle({
  id,
  startDt,
  forBlock = false,
  duration,
  minDuration = 10,
  maxDuration,
  resizeStartRef,
  setLocalDuration,
  setGlobalDuration,
  setIsResizing,
}: {
  id: number;
  startDt: moment.Moment;
  forBlock: boolean;
  duration: number;
  minDuration?: number;
  maxDuration?: number;
  resizeStartRef: React.MutableRefObject<number | null>;
  setLocalDuration: (d: number) => void;
  setGlobalDuration: (d: number) => void;
  setIsResizing: (b: boolean) => void;
}) {
  const {eventId} = useSelector(selectors.getStaticData);
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

      if (newDuration !== duration) {
        updateEntryTime(id, eventId, startDt, newDuration);
        setGlobalDuration(newDuration);
      }
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
