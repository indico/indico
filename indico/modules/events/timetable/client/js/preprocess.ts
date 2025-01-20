// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';

import {ChildEntry, DayEntries, Session} from './types';

const entryTypeMapping = {
  s: 'block',
  c: 'contrib',
  b: 'break',
};

export function preprocessSessionData(data: Record<string, any>): Record<number, Session> {
  return Object.fromEntries(
    Object.entries(data).map(([, s]) => [
      s.id,
      {
        ..._.pick(s, ['title', 'isPoster']), // TODO(Duarte) get other attrs
        textColor: s.textColor,
        backgroundColor: s.color,
      },
    ])
  );
}

export function preprocessTimetableData(
  data: any,
  eventInfo: any
): {dayEntries: DayEntries; unscheduled: any[]} {
  // console.log(data);
  // console.log('einfo', eventInfo);
  const dayEntries = {};
  for (const day in data) {
    dayEntries[day] = [];
    for (const _id in data[day]) {
      const id = parseInt(_id.slice(1), 10);
      const type = entryTypeMapping[_id[0]];
      const entry = data[day][_id];

      dayEntries[day].push({
        type,
        id,
        title: entry.title,
        startDt: moment(`${entry.startDate.date} ${entry.startDate.time}`),
        duration: entry.duration,
        x: 0,
        y: 0,
        width: 0,
        column: 0,
        maxColumn: 0,
      });

      if (entry.sessionId) {
        dayEntries[day].at(-1).sessionId = entry.sessionId;
      }

      if (type === 'break') {
        dayEntries[day].at(-1).backgroundColor = entry.color;
        dayEntries[day].at(-1).textColor = entry.textColor;
      }

      if (type === 'block') {
        const children = Object.entries(entry.entries).map(([_id, _childEntry]) => {
          const childId = parseInt(_id.slice(1), 10);

          const childEntry: ChildEntry = {
            type: entryTypeMapping[_id[0]],
            id: childId,
            title: _childEntry.title,
            startDt: moment(`${_childEntry.startDate.date} ${_childEntry.startDate.time}`),
            duration: _childEntry.duration,
            parentId: dayEntries[day].at(-1).id,
            x: 0,
            y: 0,
            width: 0,
            column: 0,
            maxColumn: 0,
          };

          if (entry.sessionId) {
            childEntry.sessionId = entry.sessionId;
          }

          return childEntry;
        });
        dayEntries[day].at(-1).children = children;
      }
    }
  }

  const unscheduled = (eventInfo.contributions || []).map(c => ({
    type: 'contrib',
    id: c.uniqueId,
    title: c.title,
    duration: c.duration,
    x: 0,
    y: 0,
    width: 0,
    column: 0,
    maxColumn: 0,
  }));
  return {dayEntries, unscheduled};
}
