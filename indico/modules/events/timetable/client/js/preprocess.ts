// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mapDataToEntry, mapDataToSession} from './mapperUtils';
import {DayEntries, Session, UnscheduledContribEntry} from './types';

export function preprocessSessionData(
  data: Record<string, Record<string, unknown>>
): Record<string, Session> {
  return Object.fromEntries(Object.entries(data).map(([, s]) => [s.id, mapDataToSession(s)]));
}

export function preprocessTimetableEntries(
  data: Record<string, unknown>,
  eventInfo: {contributions?: Record<string, unknown>[]}
): {dayEntries: DayEntries; unscheduled: UnscheduledContribEntry[]} {
  const dayEntries = Object.fromEntries(
    Object.entries(data).map(([day, entries]) => [
      day,
      Object.values(entries).map(entryData => mapDataToEntry(entryData)),
    ])
  );

  return {
    dayEntries,
    unscheduled: eventInfo.contributions.map(c => mapDataToEntry(c) as UnscheduledContribEntry),
  };
}
