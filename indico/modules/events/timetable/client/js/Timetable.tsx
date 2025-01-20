// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
// import {Checkbox} from 'semantic-ui-react';

import * as actions from './actions';
import {DayTimetable} from './DayTimetable';
import EntryDetails from './EntryDetails';
import ContributionEntryForm from './forms/ContributionEntryForm';
import * as selectors from './selectors';
import Toolbar from './Toolbar';
import {getEarliestDate} from './utils';
import {WeekTimetable} from './WeekTimetable';
import WeekViewToolbar from './WeekViewToolbar';

import './timetable.scss';
import './Timetable.module.scss';

// const localizer = momentLocalizer(moment);
// const DnDCalendar = withDragAndDrop(Calendar);

export default function Timetable() {
  const dispatch = useDispatch();
  const entries = useSelector(selectors.getDayEntries);

  // const blocks = useSelector(selectors.getBlocks);
  const selectedId = useSelector(selectors.getSelectedId);
  // const selectedId = null;

  // const draggedContribs = useSelector(selectors.getDraggedContribs);
  const [date, setDate] = useState(moment(getEarliestDate(Object.keys(entries))));
  const [placeholderEntry, setPlaceholderEntry] = useState(null);
  const currentDateEntries = entries[date.format('YYYYMMDD')];

  let selectedEntry = currentDateEntries.find(e => e.id === selectedId);
  if (!selectedEntry) {
    selectedEntry = currentDateEntries
      .flatMap(e => (e.type === 'block' ? e.children : []))
      .find(e => e.id === selectedId);
  }
  const popupsEnabled = useSelector(selectors.getPopupsEnabled);

  const useWeekView = false;

  const minHour = Math.max(
    0,
    useWeekView
      ? Math.min(
          ...Object.values(entries)
            .flat()
            .map(e => moment(e.startDt).hour())
        ) - 1
      : Math.min(...currentDateEntries.map(e => moment(e.startDt).hour())) - 1
  );
  const maxHour = Math.min(
    24,
    useWeekView
      ? Math.max(
          ...Object.values(entries)
            .flat()
            .map(e =>
              moment(e.startDt)
                .add(e.duration, 'minutes')
                .hour()
            )
        ) + 1
      : Math.max(
          ...currentDateEntries.map(e =>
            moment(e.startDt)
              .add(e.duration, 'minutes')
              .hour()
          )
        ) + 1
  );

  useEffect(() => {
    function onKeydown(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === 'z') {
        dispatch(actions.undoChange());
      } else if (e.ctrlKey && e.key === 'y') {
        dispatch(actions.redoChange());
      }
    }

    document.addEventListener('keydown', onKeydown);
    return () => document.removeEventListener('keydown', onKeydown);
  }, [dispatch]);

  return (
    <div styleName={`timetable`}>
      {/* <div style={{height: 50}}>
        <Checkbox
          toggle
          checked={popupsEnabled}
          onChange={() => dispatch(actions.experimentalTogglePopups())}
          label="Experminetal: Use popups instead of sidebar"
        />
      </div> */}
      {useWeekView && <WeekViewToolbar date={date} onNavigate={d => setDate(d)} />}
      {!useWeekView && <Toolbar date={date} onNavigate={d => setDate(d)} />}
      <div styleName="content">
        {useWeekView && <WeekTimetable minHour={0} maxHour={24} entries={entries} />}
        {!useWeekView && (
          <DayTimetable dt={date} minHour={0} maxHour={24} entries={currentDateEntries} />
        )}
        {!popupsEnabled && selectedEntry && <EntryDetails entry={selectedEntry} />}
        <ContributionEntryForm />
      </div>
    </div>
  );
}
