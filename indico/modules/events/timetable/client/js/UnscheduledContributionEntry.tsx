// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:contributions.api_manage_contrib';

import moment, {Moment} from 'moment';
import React from 'react';
import {createPortal} from 'react-dom';
import {useSelector, useDispatch} from 'react-redux';
import {Button} from 'semantic-ui-react';

import {getChangedValues, handleSubmitError} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {useDraggable, useDroppableData} from './dnd';
import {pointerInside} from './dnd/utils';
import {EntryTitle} from './Entry';
import {formatTimeRange} from './i18n';
import {mapDataToEntry} from './mapperUtils';
import {UNSCHEDULED_CONTRIB_EDIT_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {ContribId, EntryType, ReduxState} from './types';
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
  objId,
  dt,
  title,
  duration,
  sessionId,
}: {
  id: ContribId;
  objId: number;
  dt: Moment;
  title: string;
  duration: number;
  sessionId?: number;
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
      timeRange = formatTimeRange(moment.locale().replace('_', '-'), startDt, newEnd);
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
          objId={objId}
          id={id}
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
        objId={objId}
        id={id}
      />
    </div>
  );
}

export function UnscheduledContributionEntry({
  id,
  objId,
  title,
  timeRange,
  duration,
  sessionId,
  isDragging,
}: {
  id: ContribId;
  objId: number;
  title: string;
  timeRange: string;
  duration: number;
  sessionId?: number;
  isDragging?: boolean;
}) {
  const {openModal} = useModal();
  const dispatch = useDispatch<any>();
  const contrib = useSelector(selectors.getUnscheduled).find(c => c.id === id);

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
          <Button
            basic
            type="button"
            title={Translate.string('Edit contribution')}
            icon="edit"
            size="small"
            onClick={e => {
              openModal(UNSCHEDULED_CONTRIB_EDIT_MODAL, {
                eventId,
                contribId: objId,
                onSubmit: async (formData, form) => {
                  // TODO: (Ajob) Instead, maybe create a separate timetable contrib form
                  //              that disregards scheduling info like startdt. Or modify
                  //              the existing timetable manage form to allow for this use case.
                  const changedVals = getChangedValues(formData, form);
                  try {
                    await indicoAxios.patch(
                      contributionURL({event_id: eventId, contrib_id: objId}),
                      changedVals
                    );
                  } catch (err) {
                    return handleSubmitError(err);
                  }

                  const changedEntryData = mapDataToEntry(changedVals, true);
                  dispatch(
                    actions.updateUnscheduledEntry(
                      EntryType.Contribution,
                      contrib.id,
                      changedEntryData
                    )
                  );
                  e.stopPropagation();
                },
              });
            }}
          />
          <Button
            basic
            type="button"
            title={Translate.string('Delete contribution')}
            icon="trash"
            size="small"
            onClick={e => {
              e.stopPropagation();
              dispatch(actions.deleteUnscheduledContrib(objId, eventId));
            }}
          />
        </div>
      )}
    </div>
  );
}
