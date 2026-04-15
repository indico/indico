// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {Entry, EntryType, PersonLink, Session} from './types';
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
}

type MapperConfig<From, To> = MapperEntry<From, To>[];

// (Ajob) We are assigning it at the bottom
// eslint-disable-next-line prefer-const
let mapDataToPersonLink, mapPersonLinkToData;

// Mapper configurations for various timetable objects
const entryMapperConfig: MapperConfig<Record<string, unknown>, Entry> = [
  // {from: 'type', to: 'type'},
  {from: 'type', to: 'type'},
  {from: 'id', to: 'objId', toTransform: () => undefined},
  {
    from: 'id',
    to: 'id',
    fromTransform: (v: number, data) => (v ? getEntryUniqueId(data.type as EntryType, v) : null),
    toTransform: (v: string) => +v.slice(1),
  },
  {from: 'title', to: 'title'},
  {from: 'description', to: 'description'},
  {from: 'board_number', to: 'boardNumber'},
  // TODO: (Ajob) Currently we use conveners and person_links in the
  // 							back-end, and only personLinks in front-end. This is
  // 							causing inconsistency here. We should probably not
  // 							be using person_links for conveners on the front-end.
  {
    from: 'person_links',
    to: 'personLinks',
    fromTransform: p => p.map(mapDataToPersonLink),
    toTransform: p => p.map(mapPersonLinkToData),
  },
  {
    from: 'conveners',
    to: 'personLinks',
    fromTransform: p => p.map(mapDataToPersonLink),
    toTransform: p => p.map(mapPersonLinkToData),
  },
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
  {from: 'session_id', to: 'sessionId'},
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
    fromTransform: (c: {background: string; text: string}) => ({
      backgroundColor: c.background,
      color: c.text,
    }),
    toTransform: (c: {backgroundColor: string; color: string}) => ({
      background: c.backgroundColor,
      text: c.color,
    }),
  },
  {
    from: 'default_contribution_duration',
    to: 'defaultContribDurationMinutes',
    toTransform: (minutes: number) => minutes * 60,
    fromTransform: (seconds: number) => seconds / 60,
  },
];

const personLinkMapperConfig: MapperConfig<Record<string, unknown>, PersonLink> = [
  {from: 'address', to: 'address'},
  {from: 'affiliation', to: 'affiliation'},
  {from: 'affiliation_id', to: 'affiliationId'},
  {from: 'avatar_url', to: 'avatarUrl'},
  {from: 'display_order', to: 'displayOrder'},
  {from: 'email', to: 'email'},
  {from: 'first_name', to: 'firstName'},
  {from: 'last_name', to: 'lastName'},
  {from: 'name', to: 'name'},
  {from: 'person_id', to: 'personId'},
  {from: 'phone', to: 'phone'},
  {from: 'roles', to: 'roles'},
  {from: 'title', to: 'title'},
  {from: 'user_id', to: 'userId'},
  {from: 'user_identifier', to: 'userIdentifier'},
];

// Generic mapper
function createMapper<From, To>(config: MapperConfig<From, To>, defaults?: Partial<To>) {
  function mapDataToObj(data: From, partial: true): Partial<To>;
  function mapDataToObj(data: From, partial?: false): To;
  function mapDataToObj(data: From, partial = false): To | Partial<To> {
    const result: Partial<To> = defaults ? {...defaults} : {};
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

  function mapObjToData(obj: Partial<To>, partial: true): Partial<From>;
  function mapObjToData(obj: Partial<To>, partial?: false): From;
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
const {mapDataToObj: mapDataToSession, mapObjToData: mapSessionToData} = createMapper<
  Record<string, unknown>,
  Session
>(sessionMapperConfig);
({mapDataToObj: mapDataToPersonLink, mapObjToData: mapPersonLinkToData} = createMapper<
  Record<string, unknown>,
  PersonLink
>(personLinkMapperConfig));
// (Ajob) As we need to define some defaults, we need to re-apply some of the function types
const {mapObjToData: mapEntryToData} = createMapper<Record<string, unknown>, Entry>(
  entryMapperConfig
);
function mapDataToEntry(data: Record<string, unknown>, partial: true): Partial<Entry>;
function mapDataToEntry(data: Record<string, unknown>, partial?: false): Entry;
function mapDataToEntry(data: Record<string, unknown>, partial = false): Entry | Partial<Entry> {
  const entryDefaults: Partial<Record<EntryType, Partial<Entry>>> = {
    [EntryType.SessionBlock]: {children: []},
  };
  const defaults = entryDefaults[data.type as EntryType] ?? {};
  const {mapDataToObj} = createMapper<Record<string, unknown>, Entry>(entryMapperConfig, defaults);

  // (Ajob) Had to do this otherwise type complains (boolean is not specific enough)
  return partial ? mapDataToObj(data, true) : mapDataToObj(data, false);
}

export {mapDataToEntry, mapEntryToData};
export {mapDataToSession, mapSessionToData};
