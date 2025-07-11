// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';

export enum EntryType {
  Contribution = 'contrib',
  SessionBlock = 'block',
  Break = 'break',
}

export interface Session {
  id?: number;
  title: string;
  isPoster: boolean;
  textColor: string;
  backgroundColor: string;
}

export interface BaseEntry {
  type: EntryType;
  id: string;
  objId: number;
  title: string;
  duration: number;
  description: string;
}

export interface ScheduledMixin {
  startDt: Moment;
  // position information
  x: number;
  y: number;
  column: number;
  maxColumn: number;
}

export interface UnscheduledContrib extends BaseEntry {
  type: EntryType.Contribution;
  sessionId?: number;
}

export interface ContribEntry extends UnscheduledContrib, ScheduledMixin {}

export interface BreakEntry extends BaseEntry, ScheduledMixin {
  type: EntryType.Break;
  sessionId?: number;
  textColor: string;
  backgroundColor: string;
}

export interface ChildContribEntry extends ContribEntry {
  parentId: number;
}

export interface ChildBreakEntry extends BreakEntry {
  parentId: number;
}

export type ChildEntry = ChildContribEntry | ChildBreakEntry;

export interface BlockEntry extends BaseEntry, ScheduledMixin {
  type: EntryType.SessionBlock;
  sessionId: number;
  sessionTitle: string;
  children: ChildEntry[];
  conveners?: any[];
}

// TODO: (Ajob) Find correct place for these interfaces

export interface LocationParent {
  venue: string;
  room: string;
  venue_name: string;
  room_name: string;
  address: string;
  inheriting: boolean;
}

export interface RequestEntryObjectData {
  description: string;
  duration: number;
  start_dt: string;
  end_dt: string;
  event_id: number;
  location: Location;
  title: string;
  type: string;
}

export interface RequestEntryObject {
  duration: number;
  end_dt: string;
  event_id: number;
  id: number;
  object: RequestEntryObjectData;
  start_dt: string;
  type: string;
}

export type TopLevelEntry = ContribEntry | BlockEntry | BreakEntry;
export type Entry = TopLevelEntry | ChildEntry;
export type DayEntries = Record<string, TopLevelEntry[]>;

export function isChildEntry(entry: Entry): entry is ChildEntry {
  return 'parentId' in entry;
}
