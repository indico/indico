// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mapDataToEntry, mapDataToSession} from './mapperUtils';
import {Session, Entry, UnscheduledContribEntry} from './types';

export function preprocessSessionData(
  data: Record<string, Record<string, unknown>>
): Record<string, Session> {
  return Object.fromEntries(Object.entries(data).map(([, s]) => [s.id, mapDataToSession(s)]));
}

export function preprocessTimetableEntries(data: Record<string, unknown>): Entry[] {
  return Object.fromEntries(
    Object.entries(data).map(([id, entryData]) => [id, mapDataToEntry(entryData)])
  );
}

export function preprocessUnscheduledContributions(
  contributions: unknown
): UnscheduledContribEntry[] {
  return contributions.map(c => mapDataToEntry(c) as UnscheduledContribEntry);
}
