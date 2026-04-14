// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import {mapDataToEntry} from './mapperUtils';
import {
  Attachment,
  Colors,
  DayEntries,
  EntryUniqueID,
  LocationData,
  PersonLink,
  Session,
  UnscheduledContribEntry,
} from './types';

interface SchemaDate {
  date: string;
  time: string;
  tz: string;
}

interface SchemaEntry {
  startDt: SchemaDate;
  id: EntryUniqueID;
  objId: number;
  title: string;
  description?: string;
  locationData: LocationData;
  duration: number;
  colors?: Colors;
  slotTitle?: string;
  personLinks?: PersonLink[];
  // (Ajob) Attachments are not possible for breaks but we need to rework
  //        the interfaces as a whole in general.
  attachments?: Attachment[];
}

interface SchemaSession extends SchemaEntry {
  isPoster: boolean;
  defaultContribDurationMinutes: number;
  colors: Colors;
}

export function preprocessSessionData(
  data: Record<string, SchemaSession>
): Record<string, Session> {
  // @ts-expect-error number vs string mess with ids, to be fixed later...
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

export function preprocessTimetableEntries(
  data: Record<string, unknown>,
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
): {dayEntries: DayEntries; unscheduled: UnscheduledContribEntry[]} {
  const dayEntries = Object.fromEntries(
    Object.entries(data).map(([day, entries]) => [
      day,
      Object.values(entries).map((entryData: Record<string, unknown>) => mapDataToEntry(entryData)),
    ])
  );

  return {
    dayEntries,
    unscheduled: (eventInfo.contributions || []).map(
      (c: Record<string, unknown>) => mapDataToEntry(c) as UnscheduledContribEntry
    ),
  };
}
