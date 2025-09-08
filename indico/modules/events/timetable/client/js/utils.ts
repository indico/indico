// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import {useEffect, useRef} from 'react';

import {camelizeKeys} from 'indico/utils/case';

import {DEFAULT_BREAK_COLORS, DEFAULT_CONTRIB_COLORS, ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {Colors, Entry, EntryType, Session} from './types';

export const DATE_KEY_FORMAT = 'YYYYMMDD';
export const LOCAL_STORAGE_KEY = 'manageTimetableData';
export const GRID_SIZE_MINUTES = 5;
export const GRID_SIZE = minutesToPixels(GRID_SIZE_MINUTES);

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

export function getDefaultColorByType(type: EntryType) {
  return {
    [EntryType.Contribution]: DEFAULT_CONTRIB_COLORS,
    [EntryType.Break]: DEFAULT_BREAK_COLORS,
  }[type]
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

export const getEntryUniqueId = (entry): string => {
  switch (entry.type) {
    case EntryType.SessionBlock:
      return `s${entry.id}`;
    case EntryType.Contribution:
      return `c${entry.id}`;
    case EntryType.Break:
      return `b${entry.id}`;
  }
};

export const mapTTDataToEntry = (data, sessions): Entry => {
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
    code,
    keywords,
    sessionId,
    sessionBlockId,
  } = data;

  const mappedObj = {
    id: getEntryUniqueId(data),
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
    locationData: {
      address: locationData.address,
      room: locationData.roomName,
      inheriting: locationData.inheriting,
      venueName: locationData.venueName,
    },
    code,
    keywords,
    column: 0,
    maxColumn: 0,
    children: [],
    sessionId: sessionId || null,
    sessionBlockId: sessionBlockId || null,
    colors: mapTTEntryColor(data, sessions),
  };

  if (sessionBlockId) {
    mappedObj.sessionBlockId = `s${sessionBlockId}`;
  }

  return mappedObj;
};

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
