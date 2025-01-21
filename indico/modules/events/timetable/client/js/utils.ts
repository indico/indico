// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';

const GRID_SIZE_MINUTES = 5;
const GRID_SIZE = minutesToPixels(GRID_SIZE_MINUTES);

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
