// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';

type PercentWidth = number;

export interface Session {
  title: string;
  isPoster: boolean;
  textColor: string;
  backgroundColor: string;
}

interface BaseEntry {
  type: 'contrib' | 'block' | 'break';
  id: number;
  title: string;
  startDt: Moment;
  duration: number;
  // position information
  x: number;
  y: number;
  width: PercentWidth | string;
  column: number;
  maxColumn: number;
}

export interface ContribEntry extends BaseEntry {
  type: 'contrib';
  sessionId?: number;
}

export interface BlockEntry extends BaseEntry {
  type: 'block';
  sessionId: number;
  children: ChildEntry[];
}

export interface BreakEntry extends BaseEntry {
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

export type TopLevelEntry = ContribEntry | BlockEntry | BreakEntry;
export type ChildEntry = ChildContribEntry | ChildBreakEntry;
export type Entry = TopLevelEntry | ChildEntry;
export type DayEntries = Record<string, TopLevelEntry[]>;
