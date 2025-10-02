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

export type HexColor = `#${string}`;

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

export interface Colors {
  color: HexColor;
  backgroundColor: HexColor;
}

export interface LocationData {
  address: string;
  venueId?: number;
  venueName: string;
  roomId?: string;
  roomName: string;
  inheriting?: boolean;
}
export interface LocationParent {
  location_data: LocationParent;
  type: string;
  title: string;
}
export interface Attachment {
  type: 'attachment' | 'folder';
  downloadURL: string;
  id: number;
  title: string;
}

export interface Session {
  id?: number;
  title: string;
  isPoster: boolean;
  defaultContribDurationMinutes: number;
  colors: Colors;
}

export interface BaseEntry {
  type: EntryType;
  id: string;
  objId: number;
  title: string;
  duration: number;
  description: string;
  colors?: Colors;
  locationData?: LocationData;
  locationParent?: LocationParent;
  attachments?: Attachment[];
  personLinks: PersonLink[];
}

export interface ScheduledMixin {
  startDt: Moment;
  // position information
  y: number;
  column: number | null;
  maxColumn: number | null;
}

export interface UnscheduledContrib extends BaseEntry {
  type: EntryType.Contribution;
  attachments: Attachment[];
  sessionId?: number;
}

export interface ContribEntry extends UnscheduledContrib, ScheduledMixin {
  type: EntryType.Contribution;
  personLinks: PersonLink[];
}

export interface BreakEntry extends BaseEntry, ScheduledMixin {
  type: EntryType.Break;
  sessionId?: number;
  backgroundColor: string;
}

export interface ChildContribEntry extends ContribEntry {
  sessionBlockId: string;
}

export interface ChildBreakEntry extends BreakEntry {
  sessionBlockId: string;
}

export type ChildEntry = ChildContribEntry | ChildBreakEntry;

export interface BlockEntry extends BaseEntry, ScheduledMixin {
  type: EntryType.SessionBlock;
  sessionId: number;
  sessionTitle: string;
  children: ChildEntry[];
  personLinks: PersonLink[];
  attachments: Attachment[];
  childLocationParent: LocationParent;
}

export type TopLevelEntry = ContribEntry | BlockEntry | BreakEntry;
export type Entry = TopLevelEntry | ChildEntry;
export type DayEntries = Record<string, TopLevelEntry[]>;

export function isChildEntry(entry: Entry): entry is ChildEntry {
  // TODO: (Ajob) This is bypassing the 'Entry' type check because 'sessionBlockId'
  //              is not in the 'Entry' type. Find cleaner solution
  return !!entry['sessionBlockId'];
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
