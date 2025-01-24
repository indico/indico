// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';

export interface Session {
  title: string;
  isPoster: boolean;
  textColor: string;
  backgroundColor: string;
}

export interface BaseEntry {
  type: 'contrib' | 'block' | 'break';
  id: number;
  title: string;
  duration: number;
}

interface ScheduledMixin {
  startDt: Moment;
  // position information
  y: number;
  column: number;
  maxColumn: number;
}

export interface UnscheduledContrib extends BaseEntry {
  type: 'contrib';
  sessionId?: number;
}

export interface ContribEntry extends UnscheduledContrib, ScheduledMixin {}

export interface BreakEntry extends BaseEntry, ScheduledMixin {
  type: 'break';
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
  type: 'block';
  sessionId: number;
  children: ChildEntry[];
}

export type TopLevelEntry = ContribEntry | BlockEntry | BreakEntry;
export type Entry = TopLevelEntry | ChildEntry;
export type DayEntries = Record<string, TopLevelEntry[]>;

export function isChildEntry(entry: Entry): entry is ChildEntry {
  return 'parentId' in entry;
}
