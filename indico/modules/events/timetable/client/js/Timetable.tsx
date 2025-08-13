// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
// import {Checkbox} from 'semantic-ui-react';

import * as actions from './actions';
import {DayTimetable} from './DayTimetable';
import * as selectors from './selectors';
import Toolbar from './Toolbar';
import {WeekTimetable} from './WeekTimetable';

import './timetable.scss';
import './Timetable.module.scss';

export default function Timetable() {
  const dispatch = useDispatch();
  const entries = useSelector(selectors.getDayEntries);
  const eventId = useSelector(selectors.getEventId);
  const eventStartDt = useSelector(selectors.getEventStartDt);
  const eventEndDt = useSelector(selectors.getEventEndDt);
  const showAllTimeslots = useSelector(selectors.showAllTimeslots);
  const currentDay = useSelector(selectors.getCurrentDay);

  const currentDateEntries = entries[currentDay.format('YYYYMMDD')];

  const useWeekView = false;

  const minHour = showAllTimeslots
    ? 0
    : Math.max(
        Math.min(
          eventStartDt.hour(),
          ...(useWeekView
            ? Object.values(entries)
                .flat()
                .map(e => e.startDt.hour())
            : currentDateEntries.map(e => e.startDt.hour()))
        ) - 1,
        0
      );
  const maxHour = showAllTimeslots
    ? 24
    : Math.max(
        eventEndDt.hour(),
        ...(useWeekView
          ? Object.values(entries)
              .flat()
              .map(e => e.startDt.add(e.duration, 'minutes').hour())
          : currentDateEntries.map(e =>
              moment(e.startDt)
                .add(e.duration, 'minutes')
                .hour()
            ))
      );

  return (
    <div styleName="timetable">
      <GlobalEvents />
      {!useWeekView && (
        <Toolbar
          date={currentDay}
          onNavigate={d => {
            dispatch(actions.setCurrentDay(d));
          }}
        />
      )}
      <div styleName="content">
        {useWeekView && <WeekTimetable minHour={0} maxHour={24} entries={entries} />}
        {!useWeekView && (
          <DayTimetable
            dt={currentDay}
            eventId={eventId}
            minHour={minHour}
            maxHour={maxHour}
            entries={currentDateEntries}
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
