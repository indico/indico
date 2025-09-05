// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React from 'react';
import {createPortal} from 'react-dom';

import {ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {useDraggable, useDroppableData} from './dnd';
import {pointerInside} from './dnd/utils';
import {EntryTitle} from './Entry';
import {formatTimeRange} from './i18n';
import {minutesToPixels, pixelsToMinutes, snapMinutes} from './utils';

import './ContributionEntry.module.scss';
import './UnscheduledContributionEntry.module.scss';

export function DraggableUnscheduledContributionEntry({
  id,
  dt,
  title,
  duration,
  color,
  textColor,
}: {
  id: number;
  dt: Moment;
  title: string;
  duration: number;
  color?: string;
  textColor?: string;
}) {
  const droppableData = useDroppableData({id: 'calendar'});

  const draggableId = `unscheduled-${id}`;
  const {listeners, setNodeRef, transform, isDragging, rect, initialScroll, mouse, offset, ref} =
    useDraggable({
      id: draggableId,
      fixed: true,
    });

  let timeRange = `${duration} minutes`;
  if (transform && droppableData && ref.current) {
    const r = droppableData.node.current.getBoundingClientRect();
    if (pointerInside(mouse, r)) {
      const mousePositionY = mouse.y - r.top - window.scrollY;

      const start = snapMinutes(pixelsToMinutes(mousePositionY - offset.y));
      const startDt = moment(dt).startOf('day').add(start, 'minutes');
      const newEnd = moment(startDt).add(duration, 'minutes');
      timeRange = formatTimeRange('en', startDt, newEnd); // TODO: use current locale
    }
  }

  let style = {
    fontSize: 15,
    backgroundColor: color ? ENTRY_COLORS_BY_BACKGROUND[color].childColor : '#5b1aff',
    color: textColor ? textColor : undefined,
  };

  if (transform) {
    style = {
      ...style,
      transform: `translate(${transform.x}px, ${transform.y}px)`,
      zIndex: 900,
      position: 'fixed',
      top: rect.top - initialScroll.top,
      left: rect.left - initialScroll.left,
      width: rect.width,
      height: rect.height,
      borderRadius: 8,
    };
  }

  if (transform) {
    const portal = createPortal(
      <div ref={setNodeRef} style={style}>
        <UnscheduledContributionEntry
          title={title}
          timeRange={timeRange}
          duration={duration}
          color={color}
          textColor={textColor}
          isDragging={isDragging}
        />
      </div>,
      document.body
    );

    return (
      <div style={{cursor: isDragging ? 'grabbing' : 'grab', userSelect: 'none'}}>
        <div
          style={{
            border: '3px dashed #e0e1e2',
            borderRadius: '3px',
            width: rect.width,
            height: rect.height,
            pointerEvents: 'none',
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        />
        {portal}
      </div>
    );
  }

  return (
    <div ref={setNodeRef} {...listeners}>
      <UnscheduledContributionEntry
        title={title}
        timeRange={`${duration} minutes`}
        duration={duration}
        color={color}
        textColor={textColor}
        isDragging={isDragging}
      />
    </div>
  );
}

export function UnscheduledContributionEntry({
  title,
  timeRange,
  duration,
  color,
  textColor,
  isDragging,
}: {
  title: string;
  timeRange: string;
  duration: number;
  color?: string;
  textColor?: string;
  isDragging: boolean;
}) {
  const style = {
    border: '2px solid transparent',
    backgroundColor: color ? ENTRY_COLORS_BY_BACKGROUND[color].childColor : '#5b1aff',
    color: textColor ? textColor : undefined,
    fontSize: 15,
    borderRadius: 8,
    cursor: isDragging ? 'grabbing' : 'grab',
    userSelect: 'none',
    height: minutesToPixels(Math.max(duration, minutesToPixels(10)) - 1),
  };

  return (
    <div role="button" styleName="entry" style={style}>
      <EntryTitle title={title} duration={duration} timeRange={timeRange} isBreak={false} />
    </div>
  );
}
