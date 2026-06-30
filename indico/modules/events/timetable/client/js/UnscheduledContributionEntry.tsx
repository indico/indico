// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React from 'react';
import {createPortal} from 'react-dom';
import {useSelector, useDispatch} from 'react-redux';
import {Button} from 'semantic-ui-react';

import {EditContributionButton} from 'indico/modules/events/contributions/ContributionForm';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {useDraggable, useDroppableData} from './dnd';
import {pointerInside} from './dnd/utils';
import {EntryTitle} from './Entry';
import {formatTimeRange} from './i18n';
import * as selectors from './selectors';
import {EntryType, ReduxState, UnscheduledContribEntry} from './types';
import {
  getEntryColors,
  minutesToPixels,
  pixelsToMinutes,
  snapMinutes,
  MIN_DURATION,
  V_SPACE_BETWEEN_ENTRIES_PX,
} from './utils';
import './Entry.module.scss';

export function DraggableUnscheduledContributionEntry({
  id,
  dt,
  title,
  duration,
  sessionId,
  contrib,
}: {
  id: string;
  dt: Moment;
  title: string;
  duration: number;
  sessionId?: number;
  contrib: UnscheduledContribEntry;
}) {
  const droppableData = useDroppableData({id: 'calendar'});

  const draggableId = `unscheduled-${id}`;
  const {
    listeners: _listeners,
    setNodeRef,
    transform,
    isDragging,
    rect,
    initialScroll,
    mouse,
    offset,
    ref,
  } = useDraggable({
    id: draggableId,
    fixed: true,
  });

  const listeners = {
    ..._listeners,
    onMouseDown: (event: React.MouseEvent<HTMLElement>) => {
      if (event.button !== 0) {
        return;
      }

      _listeners.onMouseDown(event);
    },
  };

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

  let style: React.CSSProperties = {};

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
          sessionId={sessionId}
          isDragging={isDragging}
          contrib={contrib}
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
        sessionId={sessionId}
        isDragging={isDragging}
        contrib={contrib}
      />
    </div>
  );
}

export function UnscheduledContributionEntry({
  title,
  timeRange,
  duration,
  sessionId,
  isDragging,
  contrib,
}: {
  title: string;
  timeRange: string;
  duration: number;
  sessionId?: number;
  isDragging?: boolean;
  contrib: UnscheduledContribEntry;
}) {
  const dispatch = useDispatch<any>();

  const session = useSelector((state: ReduxState) => selectors.getSessionById(state, sessionId));
  const colors = getEntryColors({type: EntryType.Contribution}, session);
  const style = {
    border: '2px solid transparent',
    ...colors,
    cursor: isDragging ? 'grabbing' : 'grab',
    userSelect: 'none' as const,
    height: minutesToPixels(
      Math.max(duration, minutesToPixels(MIN_DURATION)) - V_SPACE_BETWEEN_ENTRIES_PX
    ),
  };

  const eventId = useSelector(selectors.getEventId);

  return (
    <div role="button" styleName="entry" style={style}>
      <EntryTitle
        title={title}
        duration={duration}
        timeRange={timeRange}
        type={EntryType.Contribution}
      />
      {!isDragging && (
        <div
          styleName="entry-actions"
          style={
            {
              '--session-color': colors.color,
              '--session-background': colors.backgroundColor,
            } as React.CSSProperties
          }
        >
          <EditContributionButton
            eventId={eventId}
            contribId={contrib.objId}
            eventTitle={contrib.title}
            trigger={
              <Button
                basic
                type="button"
                title={Translate.string('Edit contribution')}
                icon="edit"
                size="small"
              />
            }
          />
          <Button
            basic
            type="button"
            title={Translate.string('Delete contribution')}
            icon="trash"
            size="small"
            onClick={e => {
              e.stopPropagation();
              dispatch(actions.deleteUnscheduledContrib(contrib, eventId));
            }}
          />
        </div>
      )}
    </div>
  );
}
