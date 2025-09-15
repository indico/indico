// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';

import {camelizeKeys} from 'indico/utils/case';

import {ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {
  Attachments,
  ChildEntry,
  Colors,
  DayEntries,
  EntryType,
  PersonLink,
  Session,
  UnscheduledContrib,
} from './types';
import {getDefaultColorByType} from './utils';

interface SchemaDate {
  date: string;
  time: string;
  tz: string;
}

interface SchemaEntry {
  id: string;
  objId: number;
  title: string;
  colors?: Colors;
  slotTitle?: string;
}

interface SchemaSession extends SchemaEntry {
  isPoster: boolean;
}

interface SchemaBlock extends SchemaEntry {
  startDate: SchemaDate;
  duration: number;
  sessionId?: number;
  sessionTitle?: string;
  entries?: Record<string, SchemaEntry>;
  personLinks?: PersonLink[];
  attachments?: Attachments;
  address?: string;
  venueName?: string;
  room?: string;
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
        // TODO: (Duarte) get other attrs
        ..._.pick(s, ['id', 'title', 'colors', 'isPoster', 'defaultContribDurationMinutes']),
      },
    ])
  );
}

const dateToMoment = (dt: SchemaDate) => moment.tz(`${dt.date} ${dt.time}`, dt.tz);

export function preprocessTimetableEntries(
  data: Record<string, Record<string, SchemaBlock>>,
  eventInfo: {
    contributions?: {
      id: string;
      objId: number;
      title: string;
      description: string;
      duration: number;
      sessionId: number;
    }[];
  }
): {dayEntries: DayEntries; unscheduled: UnscheduledContrib[]} {
  const dayEntries = {};
  for (const day in data) {
    dayEntries[day] = [];
    for (const _id in data[day]) {
      const type = entryTypeMapping[_id[0]];
      // TODO: (Ajob) Instead of 'any', clean up interfaces and assign one for consistency
      const entry: any = data[day][_id];

      const {
        duration,
        description = '',
        address = '',
        room = '',
        location: venueName = '',
        personLinks,
        boardNumber = '',
        code,
        title,
        id,
        objId,
        attachments,
        colors = getDefaultColorByType(type),
      } = entry;

      dayEntries[day].push({
        type,
        id,
        objId,
        title,
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
        locationData: {
          address,
          room,
          venueName,
        },
        attachments,
      });

      if (entry.sessionId) {
        dayEntries[day].at(-1).sessionId = entry.sessionId;
      }

      if (type === EntryType.SessionBlock) {
        dayEntries[day].at(-1).sessionTitle = entry.sessionTitle;

        const children = Object.values(entry.entries).map((c: SchemaBlock) => {
          const childType = entryTypeMapping[c.id[0]];
          const childEntry: ChildEntry = {
            type: childType,
            objId: c.objId,
            id: c.id,
            title: c.title,
            startDt: dateToMoment(c.startDate),
            duration: c.duration,
            sessionBlockId: dayEntries[day].at(-1).id,
            x: 0,
            y: 0,
            locationData: {
              address: c.address,
              room: c.room,
              venueName: c.venueName,
            },
            width: 0,
            column: 0,
            maxColumn: 0,
            colors: c.colors,
            parent: {
              colors,
              id,
              objId,
              title,
            },
          };

          if (childType === EntryType.Contribution) {
            childEntry.attachments = c.attachments;
            childEntry.personLinks = c.personLinks;
          }

          if (entry.sessionId) {
            childEntry.sessionId = entry.sessionId;
          }

          return childEntry;
        });
        dayEntries[day].at(-1).children = children;
      }

      dayEntries[day].at(-1).colors = colors;
    }
  }

  return {
    dayEntries,
    unscheduled: (eventInfo.contributions || [])
      .map(c => camelizeKeys(c))
      .map(
        ({
          id,
          objId,
          sessionId,
          title,
          description,
          duration,
          personLinks,
          boardNumber,
          code,
          address,
          room,
          venueName,
          attachments,
        }) => ({
          type: EntryType.Contribution,
          id,
          objId,
          sessionId,
          title,
          description,
          duration,
          personLinks,
          boardNumber,
          code,
          locationData: {
            address,
            room,
            venueName,
          },
          attachments,
        })
      ),
  };
}
