// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:contributions.api_manage_contrib';

import React, {useEffect, useState} from 'react';
import {flushSync} from 'react-dom';
import {useSelector} from 'react-redux';
import {Button} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import * as actions from './actions';
import {useDraggable} from './dnd';
import {EntryTitle} from './Entry';
import {mapDataToEntry} from './mapperUtils';
import {CONFIRMATION_MODAL, UNSCHEDULED_CONTRIB_EDIT_MODAL, useModal} from './ModalContext';
import * as selectors from './selectors';
import {ContribEntry, ContribId, EntryType, ReduxState} from './types';
import {
  getEntryColors,
  minutesToPixels,
  MIN_DURATION,
  V_SPACE_BETWEEN_ENTRIES_PX,
  useTimetableDispatch,
  GRID_SIZE,
  pixelsToMinutes,
} from './utils';

import './Entry.module.scss';

export function DraggableUnscheduledContributionEntry({
  id,
  objId,
  title,
  duration,
  sessionId,
}: {
  id: ContribId;
  objId: number;
  title: string;
  duration: number;
  sessionId?: number;
}) {
  const draggableId = `unscheduled-${id}`;
  const {
    listeners: _listeners,
    setNodeRef,
    isDragging,
    ref,
  } = useDraggable({
    id: draggableId,
    fixed: true,
  });
  const dt = useSelector(selectors.getCurrentDate);
  const dispatch = useTimetableDispatch();
  const [transform, setTransform] = useState<string>();

  const listeners = {
    ..._listeners,
    onMouseDown: (event: React.MouseEvent<HTMLElement>) => {
      if (event.button !== 0 || ref.current === null) {
        return;
      }

      // Since the unscheduled entry is not necessarily aligned with the calendar grid,
      // we temporarily move it when dragging to ensure that alignment
      const calendar = document.getElementById('timetable-calendar');
      const calendarTop = calendar?.getBoundingClientRect?.()?.top ?? 0;
      const entryTop = ref.current.getBoundingClientRect().top;

      // Calculate the entry's offset from the start of the calendar
      const pixelDiff = calendarTop - entryTop;
      // Calculate the previous grid position (at each GRID_SIZE pixels)
      const yAdjustment = pixelDiff % GRID_SIZE;
      const startDt = dt
        .clone()
        .startOf('day')
        .add(pixelsToMinutes(yAdjustment - pixelDiff), 'minutes');
      dispatch(actions.updateUnscheduledEntry(EntryType.Contribution, id, {startDt}));

      // Adjust the entry's position to be at a grid position
      // When _listeners.onMouseDown is ran, the transform property must already be set
      flushSync(() => setTransform(`translateY(${yAdjustment}px)`));
      _listeners.onMouseDown(event);
    },
  };

  useEffect(() => {
    if (isDragging) {
      // Reset the entry to its normal alignement
      return () => {
        dispatch(actions.updateUnscheduledEntry(EntryType.Contribution, id, {startDt: undefined}));
        setTransform(undefined);
      };
    }
  }, [isDragging, id, dispatch]);

  return (
    <div ref={setNodeRef} {...listeners} style={{opacity: isDragging ? 0 : 1, transform}}>
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
  const dispatch = useTimetableDispatch();
  const contrib = useSelector(selectors.getUnscheduled).find(c => c.id === id)!;

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
                onSubmit: async formData => {
                  // TODO: (Ajob) Instead, maybe create a separate timetable contrib form
                  //              that disregards scheduling info like startdt. Or modify
                  //              the existing timetable manage form to allow for this use case.
                  try {
                    await indicoAxios.patch(
                      contributionURL({event_id: eventId, contrib_id: objId}),
                      formData
                    );
                  } catch (err) {
                    return handleSubmitError(err, {}, ['custom_fields']);
                  }

                  const changedEntryData = mapDataToEntry(formData, true);
                  dispatch(
                    actions.updateUnscheduledEntry(
                      EntryType.Contribution,
                      contrib.id,
                      changedEntryData as Partial<ContribEntry>
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
              openModal(CONFIRMATION_MODAL, {
                header: Translate.string('Delete contribution?'),
                description: Translate.string('Are you sure you want to delete this contribution?'),
                onConfirm: () => dispatch(actions.deleteUnscheduledContrib(objId, eventId)),
              });
            }}
          />
        </div>
      )}
    </div>
  );
}
