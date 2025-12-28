// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createSessionURL from 'indico-url:sessions.api_create_session';
import sessionURL from 'indico-url:sessions.api_manage_session';
import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import scheduleContribURL from 'indico-url:timetable.tt_schedule';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import {Moment} from 'moment';
import {Dispatch} from 'redux';
import {ThunkDispatch} from 'redux-thunk/es';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {
  TopLevelEntry,
  BlockEntry,
  BreakEntry,
  ChildBreakEntry,
  ContribEntry,
  ChildContribEntry,
  Entry,
  EntryType,
  UnscheduledContribEntry,
  Session,
  ReduxState,
} from './types';
import {getEntryURLByObjId, mapTTDataToSession} from './utils';

export const SET_DRAFT_ENTRY = 'Set draft entry';
export const SET_TIMETABLE_DATA = 'Set timetable data';
export const SET_SESSION_DATA = 'Set session data';
export const DELETE_SESSION = 'Delete session';
export const CREATE_SESSION = 'Create session';
export const EDIT_SESSION = 'Edit session';
export const SET_CURRENT_DATE = 'Set current date';
export const ADD_SESSION_DATA = 'Add session data';
export const CHANGE_ENTRY_LAYOUT = 'Change entry layout';
export const RESIZE_ENTRY = 'Resize entry';
export const SELECT_ENTRY = 'Select entry';
export const DESELECT_ENTRY = 'Deselect entry';
export const DELETE_BREAK = 'Delete break';
export const DELETE_BLOCK = 'Delete block';
export const SCHEDULE_ENTRY = 'Schedule entry';
export const UNSCHEDULE_ENTRY = 'Unschedule entry';
export const UNDO_CHANGE = 'Undo change';
export const REDO_CHANGE = 'Redo change';
export const TOGGLE_EXPAND = 'Toggle expand';
export const TOGGLE_DRAFT = 'Toggle draft mode';
export const TOGGLE_SHOW_UNSCHEDULED = 'Toggle show unscheduled';
export const CREATE_ENTRY = 'Create entry';
export const UPDATE_ENTRY = 'Update entry';
export const EDIT_ENTRY = 'Edit entry';

interface SetTimetableDataAction {
  type: typeof SET_TIMETABLE_DATA;
  data: any;
  eventInfo: any;
}

interface SetDraftEntryAction {
  type: typeof SET_DRAFT_ENTRY;
  data: TopLevelEntry | null;
}

interface ResizeEntryAction {
  type: typeof RESIZE_ENTRY;
  date: string;
  duration: number;
  entry: Entry;
}

interface ChangeEntryLayoutAction {
  type: typeof CHANGE_ENTRY_LAYOUT;
  date: string;
  entries: TopLevelEntry[];
  entry: TopLevelEntry;
  sessionBlockId?: number;
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
  unscheduled: UnscheduledContribEntry[];
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
  entry: TopLevelEntry;
  entryType: string;
  currentDay: string;
}

interface DeleteBreakAction {
  type: typeof DELETE_BREAK;
  entry: BlockEntry | BreakEntry | ChildBreakEntry;
}

interface DeleteBlockAction {
  type: typeof DELETE_BLOCK;
  entry: BlockEntry | BreakEntry | ChildBreakEntry;
}

interface UndoChangeAction {
  type: typeof UNDO_CHANGE;
}

interface RedoChangeAction {
  type: typeof REDO_CHANGE;
}

interface SetSessionDataAction {
  type: typeof SET_SESSION_DATA;
  data: any;
}

interface EditSessionAction {
  type: typeof EDIT_SESSION;
  session: Session;
}

interface CreateSessionAction {
  type: typeof CREATE_SESSION;
  session: Session;
}

interface DeleteSessionAction {
  type: typeof DELETE_SESSION;
  sessionId: number;
}

interface ToggleShowUnscheduledAction {
  type: typeof TOGGLE_SHOW_UNSCHEDULED;
}

interface SetCurrentDateAction {
  type: typeof SET_CURRENT_DATE;
  date: Moment;
  eventId: number;
}

interface ToggleExpandAction {
  type: typeof TOGGLE_EXPAND;
}

interface ToggleDraftAction {
  type: typeof TOGGLE_DRAFT;
}

export type Action =
  | SetTimetableDataAction
  | ResizeEntryAction
  | ChangeEntryLayoutAction
  | SelectEntryAction
  | DeselectEntryAction
  | ScheduleEntryAction
  | UnscheduleEntryAction
  | CreateEntryAction
  | UpdateEntryAction
  | DeleteBreakAction
  | DeleteBlockAction
  | SetDraftEntryAction
  | UndoChangeAction
  | RedoChangeAction
  | SetSessionDataAction
  | EditSessionAction
  | CreateSessionAction
  | DeleteSessionAction
  | ToggleShowUnscheduledAction
  | SetCurrentDateAction
  | ToggleExpandAction
  | ToggleDraftAction;

export function setTimetableData(data: any, eventInfo: any): SetTimetableDataAction {
  return {type: SET_TIMETABLE_DATA, data, eventInfo};
}

export function setSessionData(data: any): SetSessionDataAction {
  return {type: SET_SESSION_DATA, data};
}

export function editSession(sessionId: number, session: Partial<Session>) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {
      staticData: {eventId},
      sessions,
    } = getState();
    const url = sessionURL({event_id: eventId, session_id: sessionId});
    const newSessionObj = mapTTDataToSession(session);
    const changedSession = {...sessions[sessionId], ...newSessionObj};

    return dispatch(
      synchronizedAjaxAction(() => indicoAxios.patch(url, session), {
        type: EDIT_SESSION,
        session: changedSession,
      })
    );
  };
}

export function createSession(session: Session) {
  return async (
    dispatch: ThunkDispatch<ReduxState, unknown, Action>,
    getState: () => ReduxState
  ) => {
    const {
      staticData: {eventId},
    } = getState();
    const url = createSessionURL({event_id: eventId});

    try {
      const {data: newSession} = await indicoAxios.post(url, session);

      await dispatch({
        type: CREATE_SESSION,
        session: mapTTDataToSession(newSession),
      });
    } catch (e) {
      handleAxiosError(e);
    }
  };
}

export function deleteSession(sessionId: number) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {
      staticData: {eventId},
    } = getState();
    const url = sessionURL({event_id: eventId, session_id: sessionId});

    return dispatch(
      synchronizedAjaxAction(() => indicoAxios.delete(url), {
        type: DELETE_SESSION,
        sessionId,
      })
    );
  };
}

export function setDraftEntry(data: any): SetDraftEntryAction {
  return {type: SET_DRAFT_ENTRY, data};
}

export function changeEntryLayout(
  entry: Entry,
  entries: TopLevelEntry[],
  date: string,
  sessionBlockId?: number
) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {staticData} = getState();
    const eventId = staticData.eventId;

    const entryURL = getEntryURLByObjId(eventId, entry.type, entry.objId);

    const entryData = {
      start_dt: entry.startDt.format(),
      session_block_id: sessionBlockId,
    };

    return dispatch(
      synchronizedAjaxAction(() => indicoAxios.patch(entryURL, entryData), {
        type: CHANGE_ENTRY_LAYOUT,
        date,
        entry,
        entries,
      })
    );
  };
}

export function toggleExpand(): ToggleExpandAction {
  return {type: TOGGLE_EXPAND};
}

export function toggleDraft(): ToggleDraftAction {
  return {type: TOGGLE_DRAFT};
}

export function resizeEntry(entry: Entry, duration: number, date: string) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {staticData} = getState();
    const eventId = staticData.eventId;
    const entryURL = getEntryURLByObjId(eventId, entry.type, entry.objId);
    const entryData = {duration: duration * 60};

    const action = synchronizedAjaxAction(() => indicoAxios.patch(entryURL, entryData), {
      type: RESIZE_ENTRY,
      date,
      duration,
      entry,
    } as ResizeEntryAction);
    return dispatch(action);
  };
}

export function selectEntry(id: string): SelectEntryAction {
  return {type: SELECT_ENTRY, id};
}

export function deselectEntry(): DeselectEntryAction {
  return {type: DESELECT_ENTRY};
}

export function deleteBreak(entry: BreakEntry, eventId: number) {
  const entryURL = breakURL({event_id: eventId, break_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.delete(entryURL), {
    type: DELETE_BREAK,
    entry,
  });
}

export function deleteBlock(entry: BlockEntry, eventId: number) {
  const entryURL = sessionBlockURL({event_id: eventId, session_block_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.delete(entryURL), {
    type: DELETE_BLOCK,
    entry,
  });
}

export function scheduleEntry(
  eventId: number,
  contribId: number,
  startDt: Moment,
  entries: TopLevelEntry[],
  unscheduled: UnscheduledContribEntry[],
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

export function unscheduleEntry(entry: ContribEntry, eventId: number) {
  const entryURL = contributionURL({event_id: eventId, contrib_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.delete(entryURL), {
    type: UNSCHEDULE_ENTRY,
    entry,
  });
}

export function undoChange(): UndoChangeAction {
  return {type: UNDO_CHANGE};
}

export function redoChange(): RedoChangeAction {
  return {type: REDO_CHANGE};
}

export function toggleShowUnscheduled() {
  return {type: TOGGLE_SHOW_UNSCHEDULED};
}

function _createEntry(entryType: EntryType, entry: Entry): CreateEntryAction {
  return {type: CREATE_ENTRY, entryType, entry};
}

export function createEntry(entryType: EntryType, entry: Entry) {
  return (dispatch: Dispatch<Action>) => {
    const color = entry.colors;
    const newEntry = {...entry, ...color};
    dispatch(_createEntry(entryType, newEntry));
  };
}

export function editEntry(entryType: EntryType, entry: Entry) {
  return {type: EDIT_ENTRY, entryType, entry};
}

export function updateEntry(
  entryType: EntryType,
  entry: Entry,
  currentDay: string
): UpdateEntryAction {
  return {type: UPDATE_ENTRY, entryType, entry, currentDay};
}

export function setCurrentDate(date: Moment, eventId: number): SetCurrentDateAction {
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

  submitRequest(request: () => Promise<object>) {
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
        await requestFunc?.();
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
export function synchronizedAjaxAction(requestFunc: () => Promise<object>, action?: Action) {
  return (dispatch: Dispatch) => {
    if (action) {
      dispatch(action);
    }
    requestQueue.submitRequest(requestFunc);
  };
}
