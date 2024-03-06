// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const SET_TIMETABLE_DATA = 'Set timetable data';
export const MOVE_ENTRY = 'Move entry';
export const RESIZE_ENTRY = 'Resize entry';
export const SCROLL_NAVBAR = 'Scroll toolbar';
export const RESIZE_WINDOW = 'Resize window';
export const TOGGLE_COMPACT_MODE = 'Toggle compact mode';

export function setTimetableData(data) {
  return {type: SET_TIMETABLE_DATA, data};
}

export function moveEntry(args) {
  return {type: MOVE_ENTRY, args};
}

export function resizeEntry(args) {
  return {type: RESIZE_ENTRY, args};
}

export function scrollNavbar(offset) {
  return {type: SCROLL_NAVBAR, offset};
}

export function resizeWindow(newSize, dayIdx) {
  return {type: RESIZE_WINDOW, newSize, dayIdx};
}

export function toggleCompactMode() {
  return {type: TOGGLE_COMPACT_MODE};
}
