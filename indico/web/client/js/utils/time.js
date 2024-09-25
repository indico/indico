// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

const TIME_RE = /^((?:2[0-3])|(?:0?\d)|(?:1\d)):?([0-5]\d)$/;

export function timeStrToInt(s) {
  const match = TIME_RE.exec(s?.trim() || '');
  if (!match) {
    return;
  }
  const [hStr, mStr] = match.slice(1);
  const h = parseInt(hStr, 10);
  const m = parseInt(mStr, 10);
  return h * 60 + m;
}

export function toString(t) {
  const h = Math.floor(t / 60);
  const m = t % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

export function formatTime(t, locale, options) {
  const h = Math.floor(t / 60);
  const m = t - h;
  return new Date(0, 0, 0, h, m).toLocaleTimeString(locale, options);
}

export function normalize(s) {
  return toString(timeStrToInt(s));
}
