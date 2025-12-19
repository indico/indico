// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {ThunkDispatch} from 'redux-thunk';

import * as actions from './actions';
import {DayTimetable} from './DayTimetable';
import * as selectors from './selectors';
import Toolbar from './Toolbar';
import {EntryType, ReduxState} from './types';
import {getDateKey, minutesToPixels} from './utils';

import './timetable.scss';
import './Timetable.module.scss';

export default function Timetable() {
  const dispatch = useDispatch();
  const entries = useSelector(selectors.getDayEntries);
  const eventId = useSelector(selectors.getEventId);
  const eventStartDt = useSelector(selectors.getEventStartDt);
  const isExpanded = useSelector(selectors.getIsExpanded);
  const currentDate = useSelector(selectors.getCurrentDate);
  const currentDateEntries = entries[getDateKey(currentDate)];
  const minScrollHour = 8;
  const minHour = 0;
  const maxHour = 23;

  const _getScrollMoment = () => {
    const scrollMoment = !currentDateEntries.length
      ? moment.max(currentDate.hours(minScrollHour), eventStartDt)
      : moment.min(currentDateEntries.map(e => e.startDt));

    return moment(scrollMoment);
  };

  const _getScrollOffset = () => {
    const scrollMoment = _getScrollMoment();
    const scrollMinutes = scrollMoment.diff(moment(scrollMoment).startOf('day'), 'minutes');
    return minutesToPixels(scrollMinutes);
  };

  const initialScrollPosition = _getScrollOffset();

  return (
    <div styleName={`timetable ${isExpanded ? 'expanded' : ''}`}>
      <GlobalEvents />
      <Toolbar
        onNavigate={d => {
          dispatch(actions.setCurrentDate(d, eventId));
        }}
      />
      <div styleName="content">
        <DayTimetable
          dt={currentDate}
          eventId={eventId}
          minHour={minHour}
          maxHour={maxHour}
          entries={currentDateEntries}
          scrollPosition={initialScrollPosition}
        />
      </div>
    </div>
  );
}

function GlobalEvents() {
  const dispatch: ThunkDispatch<ReduxState, unknown, actions.Action> = useDispatch();
  const eventId = useSelector(selectors.getEventId);
  const selectedEntry = useSelector(selectors.getSelectedEntry);

  useEffect(() => {
    function onKeydown(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === 'z') {
        dispatch(actions.undoChange());
      } else if (e.ctrlKey && e.key === 'y') {
        dispatch(actions.redoChange());
      } else if (e.key === 'Escape') {
        // deselect selected entry
        if (selectedEntry) {
          dispatch(actions.deselectEntry());
        }
      } else if (e.key === 'Delete') {
        if (selectedEntry) {
          switch (selectedEntry.type) {
            case EntryType.Break: {
              dispatch(actions.deleteBreak(selectedEntry, eventId));
              break;
            }
            case EntryType.SessionBlock: {
              dispatch(actions.deleteBlock(selectedEntry, eventId));
              break;
            }
            case EntryType.Contribution: {
              dispatch(actions.unscheduleEntry(selectedEntry, eventId));
              break;
            }
          }
        }
      }
    }

    function onScroll() {
      // deselect selected entry
      if (selectedEntry) {
        dispatch(actions.deselectEntry());
      }
    }

    document.addEventListener('keydown', onKeydown);
    document.addEventListener('scroll', onScroll, true);
    return () => {
      document.removeEventListener('keydown', onKeydown);
      document.removeEventListener('scroll', onScroll, true);
    };
  }, [dispatch, eventId, selectedEntry]);

  return null;
}
