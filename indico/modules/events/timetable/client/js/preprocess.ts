// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';

import {ChildEntry, DayEntries, EntryType, Session, UnscheduledContrib} from './types';

interface SchemaDate {
  date: string;
  time: string;
  tz: string;
}

interface SchemaEntry {
  id: string;
  title: string;
  textColor?: string;
  color?: string;
  slotTitle?: string;
  conveners?: any[];
}

interface SchemaSession extends SchemaEntry {
  isPoster: boolean;
}

interface SchemaBlock extends SchemaEntry {
  startDate: SchemaDate;
  duration: number;
  sessionId?: number;
  entries?: Record<string, SchemaEntry>;
  // TODO: (Ajob) Clean up the schema or separate the attrs below
  contributionId?: number;
  breakId?: number;
  sessionBlockId?: number;
}

const entryTypeMapping = {
  s: 'block',
  c: 'contrib',
  b: 'break',
};

export function preprocessSessionData(
  data: Record<string, SchemaSession>
): Record<number, Session> {
  return Object.fromEntries(
    Object.entries(data).map(([, s]) => [
      s.id,
      {
        ..._.pick(s, ['id', 'title', 'isPoster']), // TODO: (Duarte) get other attrs
        textColor: s.textColor,
        backgroundColor: s.color,
      },
    ])
  );
}

const dateToMoment = (dt: SchemaDate) => moment.tz(`${dt.date} ${dt.time}`, dt.tz);

export function preprocessTimetableEntries(
  data: Record<string, Record<string, SchemaBlock>>,
  eventInfo: {
    contributions?: {uniqueId: number; title: string; duration: number; sessionId: number}[];
  }
): {dayEntries: DayEntries; unscheduled: UnscheduledContrib[]} {
  const dayEntries = {};
  for (const day in data) {
    dayEntries[day] = [];
    for (const _id in data[day]) {
      const id = parseInt(_id.slice(1), 10);
      const type = entryTypeMapping[_id[0]];
      const entry = data[day][_id];
      const {
        duration,
        description = '',
        address = '',
        room = '',
        location: venueName = '',
        presenters = [],
        conveners = [],
        board_number: boardNumber = '',
        code,
      } = entry as any;

      // TODO: (Ajob) Currently not passing roles as they do not exist
      //              here. Update the schema to include roles.
      const personLinks = [...presenters, ...conveners].map(
        ({affiliation, familyName: lastName, firstName, email, name, roles, avatarURL}) => ({
          affiliation,
          email,
          lastName,
          firstName,
          name,
          roles,
          avatarURL,
        })
      );

      dayEntries[day].push({
        type,
        id,
        title: entry.slotTitle ? entry.slotTitle : entry.title,
        description,
        startDt: dateToMoment(entry.startDate),
        duration,
        x: 0,
        y: 0,
        width: 0,
        column: 0,
        maxColumn: 0,
        // TODO: (Ajob) Get other attributes such as person_links
        personLinks,
        boardNumber,
        code,
        location: {
          address,
          room,
          venueName,
        },
      });

      if (entry.sessionId) {
        dayEntries[day].at(-1).sessionId = entry.sessionId;
      }

      if (entry.contributionId) {
        dayEntries[day].at(-1).contributionId = entry.contributionId;
      }

      if (entry.sessionBlockId) {
        dayEntries[day].at(-1).sessionBlockId = entry.sessionBlockId;
      }

      if (entry.breakId) {
        dayEntries[day].at(-1).breakId = entry.breakId;
      }

      if (type === EntryType.Break) {
        dayEntries[day].at(-1).backgroundColor = entry.color;
        dayEntries[day].at(-1).textColor = entry.textColor;
      } else if (type === EntryType.SessionBlock) {
        dayEntries[day].at(-1).sessionTitle = entry.title;
        dayEntries[day].at(-1).title = entry.slotTitle;

        const children = Object.entries(entry.entries).map(
          ([childId, {title, startDate, duration}]: [string, SchemaBlock]) => {
            const childEntry: ChildEntry = {
              type: entryTypeMapping[childId[0]],
              id: parseInt(childId.slice(1), 10),
              title,
              startDt: dateToMoment(startDate),
              duration,
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
          }
        );
        dayEntries[day].at(-1).children = children;
      }
    }
  }

  return {
    dayEntries,
    unscheduled: (eventInfo.contributions || []).map(c => ({
      type: 'contrib',
      id: c.uniqueId,
      sessionId: c.sessionId,
      title: c.title,
      duration: c.duration,
    })),
  };
}
