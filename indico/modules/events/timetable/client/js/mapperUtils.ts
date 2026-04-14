// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {Entry, EntryType, Session} from './types';
import {getEntryUniqueId} from './utils';

// (Ajob) We have to use AllKeys instead of keyof Entry, because keyof Entry
//        will be either keyof TopLevelEntry or keyof ChildEntry, instead of
//        a recursive union of both types and deeper nested ones.
type AllKeys<T> = T extends unknown ? keyof T : never;

interface MapperEntry<From, To> {
  from: AllKeys<From>;
  to: AllKeys<To>;
  fromTransform?: (value: any, data: From) => any;
  toTransform?: (value: any, data: To) => any;
  delete?: boolean;
}

type MapperConfig<From, To> = MapperEntry<From, To>[];

// Mapper configurations for various timetable objects
const entryMapperConfig: MapperConfig<Record<string, unknown>, Entry> = [
  {from: 'id', to: 'objId', toTransform: () => undefined},
  {
    from: 'id',
    to: 'id',
    fromTransform: (v: number, data) => (v ? getEntryUniqueId(data.type as EntryType, v) : null),
    toTransform: (v: string) => +v.slice(1),
  },
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
  {
    from: 'children',
    to: 'children',
    // TODO: (Ajob) Find a clean way to fix this use-before-define error...
    // eslint-disable-next-line no-use-before-define
    fromTransform: (children: Record<string, unknown>[]) => children.map(c => mapDataToEntry(c)),
    // eslint-disable-next-line no-use-before-define
    toTransform: (children: Entry[]) => children.map(c => mapEntryToData(c)),
  },
];

const sessionMapperConfig: MapperConfig<Record<string, unknown>, Session> = [
  {from: 'id', to: 'id'},
  {from: 'title', to: 'title'},
  {from: 'is_poster', to: 'isPoster'},
  {
    from: 'colors',
    to: 'colors',
    toTransform: (colors: {color: string; backgroundColor: string}) => ({
      text: colors.color,
      background: colors.backgroundColor,
    }),
    fromTransform: (colors: {text: string; background: string}) => ({
      color: colors.text,
      backgroundColor: colors.background,
    }),
  },
  {
    from: 'default_contribution_duration',
    to: 'defaultContribDurationMinutes',
    toTransform: (minutes: number) => minutes / 60,
    fromTransform: (seconds: number) => seconds * 60,
  },
];

// Generic mapper
function createMapper<From, To>(config: MapperConfig<From, To>) {
  function mapDataToObj(data: From, partial = false): To | Partial<To> {
    const result: Partial<To> = {};
    for (const {from, to, fromTransform} of config) {
      // TODO: (Ajob) Resolve this any issue
      if (partial && !(from in (data as any))) {
        continue;
      }
      const rawValue = data[from];
      if (rawValue === undefined) {
        continue;
      }
      const value = fromTransform ? fromTransform(rawValue, data) : rawValue;
      if (value !== undefined) {
        result[to] = value;
      }
    }
    return partial ? result : (result as To);
  }

  function mapObjToData(obj: Partial<To>, partial = false): Partial<From> | From {
    const result: Partial<From> = {};
    for (const {from, to, toTransform} of config) {
      if (partial && !(to in obj)) {
        continue;
      }
      const value = obj[to];
      if (value === undefined) {
        continue;
      }
      const rawValue = toTransform ? toTransform(value, obj as To) : value;
      result[from] = rawValue;
    }
    return partial ? result : (result as From);
  }

  return {mapDataToObj, mapObjToData};
}

// Custom mappers
const {mapDataToObj: mapDataToEntry, mapObjToData: mapEntryToData} = createMapper<
  Record<string, unknown>,
  Entry
>(entryMapperConfig);
const {mapDataToObj: mapDataToSession, mapObjToData: mapSessionToData} = createMapper<
  Record<string, unknown>,
  Session
>(sessionMapperConfig);

export {mapDataToEntry, mapEntryToData};
export {mapDataToSession, mapSessionToData};
