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

export enum PersonLinkRole {
  PRIMARY = 'primary',
  SECONDARY = 'secondary',
  SPEAKER = 'speaker',
  SUBMITTER = 'submitter',
}

export interface PersonLink {
  affiliation: string;
  avatarURL: string;
  email: string;
  emailHash: string;
  familyName: string;
  firstName: string;
  name: string;
  roles: PersonLinkRole[];
}

export interface LocationData {
  address: string;
  venueName: string;
  room: string;
  inheriting?: boolean;
}

export interface Attachments {
  files: object[];
  folders: object[];
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
  locationData?: LocationData;
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
  attachments: Attachments;
  sessionId?: number;
}

export interface ContribEntry extends UnscheduledContrib, ScheduledMixin {
  type: EntryType.Contribution;
  personLinks: PersonLink[];
}

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
  personLinks: PersonLink[];
  attachments: Attachments;
}

export type TopLevelEntry = ContribEntry | BlockEntry | BreakEntry;
export type Entry = TopLevelEntry | ChildEntry;
export type DayEntries = Record<string, TopLevelEntry[]>;

export function isChildEntry(entry: Entry): entry is ChildEntry {
  return 'parentId' in entry;
}

// Request objects (lowercase)

export interface LocationParentObj {
  venue: string;
  room: string;
  venue_name: string;
  room_name: string;
  address: string;
  inheriting: boolean;
}
