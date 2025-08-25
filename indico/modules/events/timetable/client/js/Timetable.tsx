// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import * as actions from './actions';
import {DayTimetable} from './DayTimetable';
import * as selectors from './selectors';
import Toolbar from './Toolbar';
import {getDateKey, HOUR_SIZE, minutesToPixels} from './utils';
import {WeekTimetable} from './WeekTimetable';

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

  // TODO: (Ajob) This flag is temporary and likely to be replaced with a state
  //              when we implement a weekview. This is unlikely to be the
  //              current WeekView component, which does not use day timetables.
  const useWeekView = false;
  const minScrollHour = 8;
  const minHour = 0;
  const maxHour = 23;

  const getScrollMoment = () => {
    const scrollMoment = !currentDateEntries.length
      ? moment.max(currentDate, eventStartDt)
      : moment.min(currentDateEntries.map(e => e.startDt));

    return moment(scrollMoment);
  };

  const getScrollOffset = () => {
    const scrollMoment = getScrollMoment();
    const scrollMinutes = scrollMoment.diff(moment(scrollMoment).startOf('day'), 'minutes');
    return minutesToPixels(scrollMinutes);
  };

  const initialScrollPosition = Math.max(getScrollOffset(), HOUR_SIZE * minScrollHour);

  return (
    <div styleName={`timetable ${isExpanded ? 'expanded' : ''}`}>
      <GlobalEvents />
      {!useWeekView && (
        <Toolbar
          date={currentDate}
          onNavigate={d => {
            dispatch(actions.setCurrentDate(d, eventId));
          }}
        />
      )}
      <div styleName="content">
        {useWeekView && <WeekTimetable minHour={minHour} maxHour={maxHour} entries={entries} />}
        {!useWeekView && (
          <DayTimetable
            dt={currentDate}
            eventId={eventId}
            minHour={minHour}
            maxHour={maxHour}
            entries={currentDateEntries}
            scrollPosition={initialScrollPosition}
          />
        )}
      </div>
    </div>
  );
}

function GlobalEvents() {
  const dispatch = useDispatch();
  const selectedId = useSelector(selectors.getSelectedId);

  useEffect(() => {
    function onKeydown(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === 'z') {
        dispatch(actions.undoChange());
      } else if (e.ctrlKey && e.key === 'y') {
        dispatch(actions.redoChange());
      } else if (e.key === 'Escape') {
        // deselect selected entry
        if (selectedId) {
          dispatch(actions.deselectEntry());
        }
      }
    }

    function onScroll() {
      // deselect selected entry
      if (selectedId) {
        dispatch(actions.deselectEntry());
      }
    }

    document.addEventListener('keydown', onKeydown);
    document.addEventListener('scroll', onScroll, true);
    return () => {
      document.removeEventListener('keydown', onKeydown);
      document.removeEventListener('scroll', onScroll, true);
    };
  }, [dispatch, selectedId]);

  return null;
}
