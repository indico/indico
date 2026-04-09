// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

import {Entry, EntryType} from './types';
import {getEntryUniqueId} from './utils';

// (Ajob) We have to use AllKeys instead of keyof Entry, because keyof Entry
//        will be either keyof TopLevelEntry or keyof ChildEntry, instead of
//        a recursive union of both types and deeper nested ones.
type AllKeys<T> = T extends unknown ? keyof T : never;
type EntryKey = AllKeys<Entry>;

interface MapperEntry {
  from: string;
  to: EntryKey;
  fromTransform?: (value: unknown) => unknown;
  toTransform?: (value: unknown) => unknown;
}

const mapperConfig: MapperEntry[] = [
  {from: 'id', to: 'objId'},
  {from: 'type', to: 'type'},
  {from: 'title', to: 'title'},
  {from: 'description', to: 'description'},
  {from: 'board_number', to: 'boardNumber'},
  // TODO: (Ajob) Currently we use conveners and person_links in the
  // 							back-end, and only personLinks in front-end. This is
  // 							causing inconsistency here. We should probably not
  // 							be using person_links for conveners on the front-end.
  {from: 'person_links', to: 'personLinks'},
  {from: 'conveners', to: 'personLinks'},
  {from: 'location_data', to: 'locationData'},
  {from: 'location_parent', to: 'locationParent'},
  {from: 'child_location_parent', to: 'childLocationParent'},
  {from: 'code', to: 'code'},
  {from: 'keywords', to: 'keywords'},
  {
    from: 'colors',
    to: 'colors',
    fromTransform: (c: {background: string; text: string}) => ({
      backgroundColor: c.background,
      color: c.text,
    }),
    toTransform: (c: {backgroundColor: string; color: string}) => ({
      background: c.backgroundColor,
      text: c.color,
    }),
  },
  {from: 'session_id', to: 'sessionId', fromTransform: (v: unknown) => v ?? null},
  {
    from: 'session_block_id',
    to: 'sessionBlockId',
    fromTransform: (v: number) => (v ? getEntryUniqueId(EntryType.SessionBlock, v) : null),
    toTransform: (v: string) => +v.slice(1),
  },
  {
    from: 'duration',
    to: 'duration',
    fromTransform: (v: unknown) => (typeof v === 'number' ? v / 60 : v),
    toTransform: (v: unknown) => (typeof v === 'number' ? v * 60 : v),
  },
  {
    from: 'start_dt',
    to: 'startDt',
    fromTransform: (v: unknown) => (typeof v === 'string' ? moment(v) : v),
    toTransform: (v: unknown) => (v as moment.Moment)?.toISOString?.() ?? v,
  },
];

export function mapDataToEntry(data: Record<string, unknown>, partial: true): Partial<Entry>;
export function mapDataToEntry(data: Record<string, unknown>, partial?: false): Entry;
export function mapDataToEntry(
  data: Record<string, unknown>,
  partial = false
): Entry | Partial<Entry> {
  const result: Partial<Entry> = {};

  for (const {from, to, fromTransform} of mapperConfig) {
    const rawValue = data[from];
    if (rawValue === undefined) {
      continue;
    }
    if (partial && !Object.prototype.hasOwnProperty.call(data, from)) {
      continue;
    }

    const value = fromTransform ? fromTransform(rawValue) : camelizeKeys(rawValue);
    if (value !== undefined) {
      result[to] = value;
    }
  }

  if (data.type && data.id) {
    result.id = getEntryUniqueId(data.type as EntryType, data.id as number);
  }

  if (!partial) {
    Object.assign(result, {
      x: 0,
      y: 0,
      column: 0,
      maxColumn: 0,
      children: [],
    });
  }

  return result;
}

export function mapEntryToData(data: Partial<Entry>, partial = false): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  for (const {from, to, toTransform} of mapperConfig) {
    const value = data[to];
    if (value === undefined) {
      continue;
    }
    if (partial && !Object.prototype.hasOwnProperty.call(data, to)) {
      continue;
    }
    const rawValue = toTransform ? toTransform(value) : snakifyKeys(value);
    result[from] = rawValue;
  }

  return result;
}
