// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const SET_TIMETABLE_DATA = 'Set timetable data';
export const MOVE_ENTRY = 'Move entry';
export const RESIZE_ENTRY = 'Resize entry';
export const SELECT_ENTRY = 'Select entry';
export const DELETE_ENTRY = 'Delete entry';
export const DRAG_UNSCHEDULED_CONTRIB = 'Drag unscheduled contribution';
export const SCHEDULE_CONTRIB = 'Schedule contribution';
export const CHANGE_COLOR = 'Change color';
export const UNDO_CHANGE = 'Undo change';
export const REDO_CHANGE = 'Redo change';
export const SAVE_CHANGES = 'Save changes';
export const SCROLL_NAVBAR = 'Scroll toolbar';
export const RESIZE_WINDOW = 'Resize window';
export const SET_DISPLAY_MODE = 'Set display mode';
export const TOGGLE_SHOW_UNSCHEDULED = 'Toggle show unscheduled';
export const ADD_ENTRY = 'Add entry';
export const EDIT_ENTRY = 'Edit entry';
export const CLOSE_MODAL = 'Close modal';

export function setTimetableData(data) {
  return {type: SET_TIMETABLE_DATA, data};
}

export function moveEntry(args) {
  return {type: MOVE_ENTRY, args};
}

export function resizeEntry(args) {
  return {type: RESIZE_ENTRY, args};
}

export function selectEntry(entry) {
  return {type: SELECT_ENTRY, entry};
}

export function deleteEntry(entry) {
  return {type: DELETE_ENTRY, entry};
}

export function dragUnscheduledContrib(contribId) {
  return {type: DRAG_UNSCHEDULED_CONTRIB, contribId};
}

export function scheduleContrib(contrib, args) {
  return {type: SCHEDULE_CONTRIB, contrib, args};
}

export function changeColor(color) {
  return {type: CHANGE_COLOR, color};
}

export function undoChange() {
  return {type: UNDO_CHANGE};
}

export function redoChange() {
  return {type: REDO_CHANGE};
}

export function saveChanges() {
  return {type: SAVE_CHANGES};
}

export function scrollNavbar(offset) {
  return {type: SCROLL_NAVBAR, offset};
}

export function resizeWindow(newSize, dayIdx) {
  return {type: RESIZE_WINDOW, newSize, dayIdx};
}

export function setDisplayMode(mode) {
  return {type: SET_DISPLAY_MODE, mode};
}

export function toggleShowUnscheduled() {
  return {type: TOGGLE_SHOW_UNSCHEDULED};
}

export function addEntry(entryType) {
  return {type: ADD_ENTRY, entryType};
}

export function editEntry(entryType, entry) {
  return {type: EDIT_ENTRY, entryType, entry};
}

export function closeModal() {
  return {type: CLOSE_MODAL};
}
