// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Entry, Session} from './types';
import moment, {Moment} from 'moment';

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

// Data mapping functions
export const mapPersonLinkToSchema = data => ({
  title: data.title,
  name: data.name,
  first_name: data.firstName,
  last_name: data.lastName,
  affiliation: data.affiliation,
  affiliation_id: data.affiliationId,
  email: data.email,
  address: data.address,
  phone: data.phone,
  roles: data.roles,
  type: data.type,
  avatar_url: data.avatarURL,
});

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
