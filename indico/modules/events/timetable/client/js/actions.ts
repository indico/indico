// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import scheduleContribURL from 'indico-url:timetable.tt_schedule';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import moment, {Moment} from 'moment';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {
  TopLevelEntry,
  BlockEntry,
  BreakEntry,
  ChildBreakEntry,
  ContribEntry,
  ChildContribEntry,
  UnscheduledContrib,
  EntryType,
} from './types';

export const SET_DRAFT_ENTRY = 'Set draft entry';
export const SET_TIMETABLE_DATA = 'Set timetable data';
export const SET_SESSION_DATA = 'Set session data';
export const SET_CURRENT_DATE = 'Set current date';
export const ADD_SESSION_DATA = 'Add session data';
export const MOVE_ENTRY = 'Move entry';
export const RESIZE_ENTRY = 'Resize entry';
export const SELECT_ENTRY = 'Select entry';
export const DESELECT_ENTRY = 'Deselect entry';
export const DELETE_BREAK = 'Delete break';
export const DELETE_BLOCK = 'Delete block';
export const SCHEDULE_ENTRY = 'Schedule entry';
export const UNSCHEDULE_ENTRY = 'Unschedule entry';
export const CHANGE_COLOR = 'Change color';
export const UNDO_CHANGE = 'Undo change';
export const REDO_CHANGE = 'Redo change';
export const DISMISS_ERROR = 'Dismiss error';
export const SCROLL_NAVBAR = 'Scroll toolbar';
export const TOGGLE_EXPAND = 'Toggle expand';
export const TOGGLE_DRAFT = 'Toggle draft mode';
export const TOGGLE_SHOW_UNSCHEDULED = 'Toggle show unscheduled';
export const CREATE_ENTRY = 'Create entry';
export const UPDATE_ENTRY = 'Update entry';
export const EDIT_ENTRY = 'Edit entry';

interface SetDraftEntryAction {
  type: typeof SET_DRAFT_ENTRY;
  data: TopLevelEntry | null;
}

interface ResizeEntryAction {
  type: typeof RESIZE_ENTRY;
  date: string;
  id: string;
  duration: number;
  parentId?: string;
}

interface MoveEntryAction {
  type: typeof MOVE_ENTRY;
  date: string;
  entries: TopLevelEntry[];
}

interface SelectEntryAction {
  type: typeof SELECT_ENTRY;
  id: string;
}

interface DeselectEntryAction {
  type: typeof DESELECT_ENTRY;
}

interface ScheduleEntryAction {
  type: typeof SCHEDULE_ENTRY;
  date: string;
  entries: TopLevelEntry[];
  unscheduled: UnscheduledContrib[];
}

interface UnscheduleEntryAction {
  type: typeof UNSCHEDULE_ENTRY;
  entry: ContribEntry | ChildContribEntry;
  eventId: number;
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
  eventId: number;
}

interface DeleteBlockAction {
  type: typeof DELETE_BLOCK;
  entry: BlockEntry | BreakEntry | ChildBreakEntry;
  eventId: number;
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

export function moveEntry(entry, eventId, entries: TopLevelEntry[], date: string) {
  let entryURL: string;

  switch (entry.type) {
    case EntryType.Break:
      entryURL = breakURL({event_id: eventId, break_id: entry.objId});
      break;
    case EntryType.SessionBlock:
      entryURL = sessionBlockURL({event_id: eventId, session_block_id: entry.objId});
      break;
    default:
      entryURL = contributionURL({event_id: eventId, contrib_id: entry.objId});
  }

  const entryData = {start_dt: moment(entry.startDt).format('YYYY-MM-DDTHH:mm:ss')};

  return synchronizedAjaxAction(() => indicoAxios.patch(entryURL, entryData), {
    type: MOVE_ENTRY,
    date,
    entries,
  });
}

export function toggleExpand() {
  return {type: TOGGLE_EXPAND};
}

export function toggleDraft() {
  return {type: TOGGLE_DRAFT};
}

export function resizeEntry(
  date: string,
  id: string,
  duration: number,
  parentId?: string
): ResizeEntryAction {
  return {type: RESIZE_ENTRY, date, id, duration, parentId};
}

export function selectEntry(id: string): SelectEntryAction {
  return {type: SELECT_ENTRY, id};
}

export function deselectEntry(): DeselectEntryAction {
  return {type: DESELECT_ENTRY};
}

// TODO: (Marina) Look into ThunkActions for typing
export function deleteBreak(entry, eventId) {
  const entryURL = breakURL({event_id: eventId, break_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.delete(entryURL), {
    type: DELETE_BREAK,
    entryURL,
    entry,
  });
}

export function deleteBlock(entry, eventId) {
  const entryURL = sessionBlockURL({event_id: eventId, session_block_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.delete(entryURL), {
    type: DELETE_BLOCK,
    entryURL,
    entry,
  });
}

export function scheduleEntry(
  eventId: number,
  contribId: number,
  startDt: Moment,
  entries: TopLevelEntry[],
  unscheduled: UnscheduledContrib[],
  blockId?: number
) {
  const scheduleURL = scheduleContribURL(
    blockId ? {event_id: eventId, block_id: blockId} : {event_id: eventId}
  );
  return synchronizedAjaxAction(
    () =>
      indicoAxios.post(scheduleURL, {
        contribs: [{contrib_id: contribId, start_dt: startDt.toISOString()}],
      }),
    {
      type: SCHEDULE_ENTRY,
      date: startDt.format('YYYYMMDD'),
      entries,
      unscheduled,
    }
  );
}

export function unscheduleEntry(entry, eventId) {
  const entryURL = contributionURL({event_id: eventId, contrib_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.delete(entryURL), {
    type: UNSCHEDULE_ENTRY,
    entryURL,
    entry,
  });
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

export function toggleShowUnscheduled() {
  return {type: TOGGLE_SHOW_UNSCHEDULED};
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

export function setCurrentDate(date: Moment, eventId: number) {
  return {type: SET_CURRENT_DATE, date, eventId};
}

/**
 * Manages a queue of requests to be processed in order.
 * This ensures all timetable requests are handled sequentially.
 */
 // TODO(tomas): On error, we just call `handleAxiosError` for now.
 // In the future, we might consider some undo mechanism.
class RequestQueue {
  requests: (() => Promise<object>)[];
  working: boolean;

  constructor() {
    this.requests = [];
    this.working = false;
  }

  submitRequest(request) {
    this.requests.push(request);
    if (!this.working) {
      this._processRequests().catch(error => {
        console.error('Error processing request queue:', error);
      });
    }
  }

  async _processRequests() {
    this.working = true;
    while (this.requests.length) {
      const requestFunc = this.requests.shift();
      try {
        await requestFunc();
      } catch (error) {
        handleAxiosError(error, true);
      }
    }
    this.working = false;
  }
}

const requestQueue = new RequestQueue();

/**
 * Dispatch an action immediately and submit the fetch request to the queue.
 *
 * @param requestFunc Function that does the AJAX request (typically an indicoAxios call).
 * @param action Action to dispatch immediately before the request.
 */
export function synchronizedAjaxAction(requestFunc: () => Promise<object>, action?: object) {
  return dispatch => {
    if (action) {
      dispatch(action);
    }
    requestQueue.submitRequest(requestFunc);
  };
}
