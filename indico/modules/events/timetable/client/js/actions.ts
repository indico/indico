// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

import {
  TopLevelEntry,
  BlockEntry,
  BreakEntry,
  ChildBreakEntry,
  ContribEntry,
  ChildContribEntry,
} from './types';

export const SET_DRAFT_ENTRY = 'Set draft entry';
export const SET_TIMETABLE_DATA = 'Set timetable data';
export const SET_SESSION_DATA = 'Set session data';
export const ADD_SESSION_DATA = 'Add session data';
export const MOVE_ENTRY = 'Move entry';
export const RESIZE_ENTRY = 'Resize entry';
export const SELECT_ENTRY = 'Select entry';
export const DESELECT_ENTRY = 'Deselect entry';
export const DELETE_BREAK = 'Delete break';
export const DELETE_BLOCK = 'Delete block';
export const DRAG_UNSCHEDULED_CONTRIBS = 'Drag unscheduled contributions';
export const DROP_UNSCHEDULED_CONTRIBS = 'Drop unscheduled contributions';
export const SCHEDULE_CONTRIBS = 'Schedule contributions';
export const SCHEDULE_ENTRY = 'Schedule entry';
export const UNSCHEDULE_ENTRY = 'Unschedule entry';
export const CHANGE_COLOR = 'Change color';
export const UNDO_CHANGE = 'Undo change';
export const REDO_CHANGE = 'Redo change';
export const DISMISS_ERROR = 'Dismiss error';
export const SCROLL_NAVBAR = 'Scroll toolbar';
export const RESIZE_WINDOW = 'Resize window';
export const SET_DISPLAY_MODE = 'Set display mode';
export const TOGGLE_SHOW_UNSCHEDULED = 'Toggle show unscheduled';
export const TOGGLE_SHOW_ALL_TIMESLOTS = 'Toggle show all timeslots';
export const ADD_ENTRY = 'Add entry';
export const CREATE_ENTRY = 'Create entry';
export const UPDATE_ENTRY = 'Update entry';
export const EDIT_ENTRY = 'Edit entry';
export const CLOSE_MODAL = 'Close modal';
export const EXPERIMENTAL_TOGGLE_POPUPS = 'Experimental toggle popups';

interface SetDraftEntryAction {
  type: typeof SET_DRAFT_ENTRY;
  data: TopLevelEntry | null;
}

interface ResizeEntryAction {
  type: typeof RESIZE_ENTRY;
  date: string;
  id: number;
  duration: number;
  parentId?: number;
}

interface MoveEntryAction {
  type: typeof MOVE_ENTRY;
  date: string;
  entries: TopLevelEntry[];
}

interface SelectEntryAction {
  type: typeof SELECT_ENTRY;
  id: number;
}

interface DeselectEntryAction {
  type: typeof DESELECT_ENTRY;
}

interface ScheduleEntryAction {
  type: typeof SCHEDULE_ENTRY;
  date: string;
  entries: TopLevelEntry[];
  unscheduled: any[];
}

interface UnscheduleEntryAction {
  type: typeof UNSCHEDULE_ENTRY;
  entry: ContribEntry | ChildContribEntry;
}

interface CreateEntryAction {
  type: typeof CREATE_ENTRY;
  entryType: string;
  entry: TopLevelEntry;
}

interface UpdateEntryAction {
  type: typeof UPDATE_ENTRY;
  entryType: string;
  entry: TopLevelEntry;
}

interface DeleteBreakAction {
  type: typeof DELETE_BREAK;
  entry: BlockEntry | BreakEntry | ChildBreakEntry;
}

interface DeleteBlockAction {
  type: typeof DELETE_BLOCK;
  id: number;
}

export type Action =
  | ResizeEntryAction
  | MoveEntryAction
  | SelectEntryAction
  | DeselectEntryAction
  | ScheduleEntryAction
  | UnscheduleEntryAction
  | CreateEntryAction
  | UpdateEntryAction
  | DeleteBreakAction
  | DeleteBlockAction
  | SetDraftEntryAction;

export function setTimetableData(data, eventInfo) {
  return {type: SET_TIMETABLE_DATA, data, eventInfo};
}

export function setSessionData(data) {
  return {type: SET_SESSION_DATA, data};
}

export function addSessionData(data) {
  return {type: ADD_SESSION_DATA, data};
}

export function setDraftEntry(data): SetDraftEntryAction {
  return {type: SET_DRAFT_ENTRY, data};
}

export function moveEntry(date: string, entries: TopLevelEntry[]): MoveEntryAction {
  return {type: MOVE_ENTRY, date, entries};
}

export function resizeEntry(
  date: string,
  id: number,
  duration: number,
  parentId?: number
): ResizeEntryAction {
  return {type: RESIZE_ENTRY, date, id, duration, parentId};
}

export function selectEntry(id: number): SelectEntryAction {
  return {type: SELECT_ENTRY, id};
}

export function deselectEntry(): DeselectEntryAction {
  return {type: DESELECT_ENTRY};
}

export function deleteBreak(entryURL, entry): DeleteBreakAction {
  return ajaxAction(() => indicoAxios.delete(entryURL), null, () => ({
    type: DELETE_BREAK,
    entryURL,
    entry,
  }));
}

export function deleteBlock(entryURL, entry): DeleteBlockAction {
  return ajaxAction(() => indicoAxios.delete(entryURL), null, () => ({
    type: DELETE_BLOCK,
    entryURL,
    entry,
  }));
}

export function dragUnscheduledContribs(contribIds) {
  return {type: DRAG_UNSCHEDULED_CONTRIBS, contribIds};
}

export function dropUnscheduledContribs(contribs, args) {
  return {type: DROP_UNSCHEDULED_CONTRIBS, contribs, args};
}

export function scheduleContribs(contribs, gap, startDt, dt) {
  return {type: SCHEDULE_CONTRIBS, contribs, gap, startDt, dt};
}

export function scheduleEntry(
  date: string,
  entries: TopLevelEntry[],
  unscheduled: any[]
): ScheduleEntryAction {
  return {type: SCHEDULE_ENTRY, date, entries, unscheduled};
}

export function unscheduleEntry(entryURL, entry: ContribEntry): UnscheduleEntryAction {
  return ajaxAction(() => indicoAxios.delete(entryURL), null, () => ({
    type: UNSCHEDULE_ENTRY,
    entryURL,
    entry,
  }));
}

export function changeColor(sessionId, color) {
  return {type: CHANGE_COLOR, sessionId, color};
}

export function undoChange() {
  return {type: UNDO_CHANGE};
}

export function redoChange() {
  return {type: REDO_CHANGE};
}

export function dismissError() {
  return {type: DISMISS_ERROR};
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

export function toggleShowAllTimeslots() {
  return {type: TOGGLE_SHOW_ALL_TIMESLOTS};
}

// TODO: (Ajob) Evaluate addEntry and editEntry vs createEntry and updateEntry,
//              the latter two were implemented later and might be duplicate

export function addEntry(entryType) {
  return {type: ADD_ENTRY, entryType};
}

export function createEntry(entryType, entry) {
  return {type: CREATE_ENTRY, entryType, entry};
}

export function editEntry(entryType, entry) {
  return {type: EDIT_ENTRY, entryType, entry};
}

export function updateEntry(entryType, entry) {
  return {type: UPDATE_ENTRY, entryType, entry};
}

export function closeModal() {
  return {type: CLOSE_MODAL};
}

export function experimentalTogglePopups() {
  return {type: EXPERIMENTAL_TOGGLE_POPUPS};
}

// redux actions
export const REGISTER_DROPPABLE = 'REGISTER_DROPPABLE';
export const UNREGISTER_DROPPABLE = 'UNREGISTER_DROPPABLE';
export const SET_DROPPABLE_DATA = 'SET_DROPPABLE_DATA';
export const REGISTER_DRAGGABLE = 'REGISTER_DRAGGABLE';
export const UNREGISTER_DRAGGABLE = 'UNREGISTER_DRAGGABLE';
export const REGISTER_ON_DROP = 'REGISTER_ON_DROP';

export const registerDroppable = (id: string, node: HTMLElement) => ({
  type: REGISTER_DROPPABLE,
  id,
  node,
});

export const unregisterDroppable = (id: string) => ({
  type: UNREGISTER_DROPPABLE,
  id,
});

export const setDroppableData = (id: string, data: any) => ({
  type: SET_DROPPABLE_DATA,
  id,
  data,
});

export const registerDraggable = (id: string) => ({
  type: REGISTER_DRAGGABLE,
  id,
});

export const unregisterDraggable = (id: string) => ({
  type: UNREGISTER_DRAGGABLE,
  id,
});

export const registerOnDrop = (onDrop: (draggableId: string, droppableId: string) => void) => ({
  type: REGISTER_ON_DROP,
  onDrop,
});
