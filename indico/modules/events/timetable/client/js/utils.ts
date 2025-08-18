// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import {useEffect, useRef} from 'react';

import {camelizeKeys} from 'indico/utils/case';

import {Entry, EntryType, Session} from './types';

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

export const mapTTDataToEntry = (data): Entry => {
  const {
    type,
    startDt,
    id,
    duration,
    title,
    description,
    conveners,
    personLinks,
    colors,
    boardNumber,
    locationData,
    code,
    keywords,
    sessionId,
    parentId,
  } = camelizeKeys(data);

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
    locationData,
    code,
    keywords,
    column: 0,
    maxColumn: 0,
    children: [],
    colors,
    textColor: colors ? colors.text : '',
    backgroundColor: colors ? colors.background : '',
    sessionId: sessionId || null,
  };

  if (parentId) {
    mappedObj.parentId = parentId;
  }

  return mappedObj;
};

const DEFAULT_CONTRIB_TEXT_COLOR = '#ffffff';
const DEFAULT_CONTRIB_BACKGROUND_COLOR = '#5b1aff';

export function getEntryColor(
  entry: Entry,
  sessions: Record<number, Session>
): {textColor: string; backgroundColor: string} {
  if (entry.type === 'break') {
    return {textColor: entry.textColor, backgroundColor: entry.backgroundColor};
  }

  if (entry.type === 'contrib' && !entry.sessionId) {
    return {
      textColor: DEFAULT_CONTRIB_TEXT_COLOR,
      backgroundColor: DEFAULT_CONTRIB_BACKGROUND_COLOR,
    };
  }

  const session = sessions[entry.sessionId];
  console.assert(session, `Session ${entry.sessionId} not found for entry ${entry.id}`);

  return {
    textColor: session.textColor,
    backgroundColor: session.backgroundColor,
  };
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

// Local storage utils
export function setCurrentDateLocalStorage(date: Moment, eventId: number) {
  const dtKeyObj = {currentDtKey: getDateKey(date)};

  const manageTimetableData = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}');
  manageTimetableData[eventId] = {...(manageTimetableData[eventId] || {}), ...dtKeyObj};
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(manageTimetableData));
}

export function getCurrentDateLocalStorage(eventId: number) {
  const manageTimetableData = JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}');
  const dt = (manageTimetableData[eventId] || {}).currentDtKey;
  return dt ? moment(dt, DATE_KEY_FORMAT) : null;
}
