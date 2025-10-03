// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import moment, {Moment} from 'moment';
import {useEffect, useRef} from 'react';
import {SemanticICONS} from 'semantic-ui-react';

import {camelizeKeys} from 'indico/utils/case';

import {DEFAULT_BREAK_COLORS, DEFAULT_CONTRIB_COLORS, ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {BlockEntry, Colors, Entry, EntryType, Session} from './types';

export const DATE_KEY_FORMAT = 'YYYYMMDD';
export const LOCAL_STORAGE_KEY = 'manageTimetableData';
export const GRID_SIZE_MINUTES = 5;
export const GRID_SIZE = minutesToPixels(GRID_SIZE_MINUTES);
export const HOUR_SIZE = minutesToPixels(60);
export const DAY_SIZE = 24 * HOUR_SIZE;

export function snapPixels(x: number) {
  return Math.ceil(x / GRID_SIZE) * GRID_SIZE;
}

export function snapMinutes(x: number) {
  return Math.ceil(x / GRID_SIZE_MINUTES) * GRID_SIZE_MINUTES;
}

export function minutesToPixels(minutes: number) {
  return Math.round(minutes * 2);
}

export function pixelsToMinutes(pixels: number) {
  return Math.round(pixels / 2);
}

export function isWithinLimits(limits: [number, number], y: number, offsets = [0, 0]) {
  return y > limits[0] + offsets[0] && y < limits[1] - offsets[1];
}

export function minutesFromStartOfDay(dt: Moment) {
  return moment(dt).diff(moment(dt).startOf('day'), 'minutes');
}

export function lcm(...args: number[]) {
  return args.reduce((acc, curr) => (acc * curr) / gcd(acc, curr), 1);
}

function gcd(a: number, b: number) {
  a = Math.abs(a);
  b = Math.abs(b);
  while (b) {
    const t = b;
    b = a % b;
    a = t;
  }
  return a;
}

export const getEntryURLByObjId = (
  eventId: number,
  entryType: EntryType,
  entryObjId: number
): string => {
  return {
    [EntryType.Break]: breakURL({event_id: eventId, break_id: entryObjId}),
    [EntryType.SessionBlock]: sessionBlockURL({event_id: eventId, session_block_id: entryObjId}),
    [EntryType.Contribution]: contributionURL({event_id: eventId, contrib_id: entryObjId}),
  }[entryType];
};

export function getDefaultColorByType(type: EntryType): Colors {
  return {
    [EntryType.Contribution]: DEFAULT_CONTRIB_COLORS,
    [EntryType.Break]: DEFAULT_BREAK_COLORS,
  }[type];
}

export function mapTTEntryColor(dbEntry, sessions: Record<number, Session> = {}): Colors {
  const {sessionId, type, colors} = dbEntry;

  const fallbackColor = colors
    ? {color: colors.text, backgroundColor: colors.background}
    : getDefaultColorByType(dbEntry.type);

  if (type === EntryType.SessionBlock) {
    return sessions[sessionId].colors ?? fallbackColor;
  }

  if (sessionId) {
    const session = sessions[sessionId];
    console.assert(session, `Session ${dbEntry.sessionId} not found for entry ${dbEntry.id}`);
    return ENTRY_COLORS_BY_BACKGROUND[session.colors.backgroundColor];
  }

  return fallbackColor;
}

export const getEntryUniqueId = (type: EntryType, id: string): string => {
  switch (type) {
    case EntryType.SessionBlock:
      return `s${id}`;
    case EntryType.Contribution:
      return `c${id}`;
    case EntryType.Break:
      return `b${id}`;
  }
};

export const mapTTDataToEntry = (
  data,
  sessions: Record<number, Session> = {},
  parent?: Partial<BlockEntry>
): Entry => {
  data = camelizeKeys(data);
  const {
    type,
    startDt,
    id,
    duration,
    title,
    description,
    conveners,
    personLinks,
    boardNumber,
    locationData,
    locationParent,
    childLocationParent,
    code,
    keywords,
    sessionId,
    sessionTitle,
    sessionBlockId,
  } = data;

  const mappedObj = {
    id: getEntryUniqueId(type, id),
    objId: id,
    type,
    title,
    description,
    duration: duration / 60,
    startDt: moment(startDt),
    x: 0,
    y: 0,
    personLinks: personLinks || conveners || [],
    boardNumber,
    locationData,
    locationParent,
    childLocationParent,
    code,
    keywords,
    column: 0,
    maxColumn: 0,
    children: [],
    sessionId: sessionId || null,
    sessionBlockId: sessionBlockId || null,
    sessionTitle: sessionTitle || '',
    colors: mapTTEntryColor(data, sessions),
    ...(sessionId && {sessionId}),
    ...(sessionBlockId && {
      sessionBlockId: getEntryUniqueId(EntryType.SessionBlock, sessionBlockId),
    }),
    ...(parent && {
      parent: {
        id: parent.id,
        objId: parent.objId,
        colors: parent.colors,
        title: parent.title,
      },
    }),
  };

  return mappedObj;
};

export function getIconByEntryType(type: EntryType) {
  return {
    [EntryType.Break]: 'coffee',
    [EntryType.Contribution]: 'file alternate outline',
    [EntryType.SessionBlock]: 'calendar alternate outline',
  }[type] as SemanticICONS;
}

export function formatBlockTitle(sessionTitle: string, blockTitle: string) {
  return blockTitle ? `${sessionTitle}: ${blockTitle}` : sessionTitle;
}

/*
 * Custom hook to log changes to props.
 * Useful for figuring out why a component is re-rendering.
 */
export function useTraceUpdate(props) {
  const prev = useRef(props);
  useEffect(() => {
    const changedProps = Object.entries(props).reduce((ps, [k, v]) => {
      if (prev.current[k] !== v) {
        ps[k] = [prev.current[k], v];
      }
      return ps;
    }, {});
    if (Object.keys(changedProps).length > 0) {
      console.log('Changed props:', changedProps);
    }
    prev.current = props;
  });
}

export function getDateKey(date: Moment) {
  return date.format(DATE_KEY_FORMAT);
}

/*
 * Gives the difference between two dates without modifying given dates. Takes into
 * account cases where two dates might be within 24 hours of each other.
 */
export function getDiffInDays(dt1: Moment, dt2: Moment) {
  dt1 = moment(dt1).startOf('day');
  dt2 = moment(dt2).startOf('day');

  return Math.abs(dt1.diff(dt2, 'day'));
}

// Local storage utils
export function setCurrentDateLocalStorage(date: Moment, eventId: number) {
  const manageTimetableData = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}');
  manageTimetableData[eventId] = {
    ...(manageTimetableData[eventId] || {}),
    currentDtKey: getDateKey(date),
  };
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(manageTimetableData));
}

export function getCurrentDateLocalStorage(eventId: number) {
  const manageTimetableData = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}');
  const dt = (manageTimetableData[eventId] || {}).currentDtKey;
  return dt ? moment(dt, DATE_KEY_FORMAT) : null;
}

export function shiftEntries<T extends Entry>(entries: T[], deltaMinutes: number): T[] {
  return entries.map(child => ({
    ...child,
    startDt: moment(child.startDt).add(deltaMinutes, 'minutes'),
  }));
}
