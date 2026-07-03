// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createSessionURL from 'indico-url:sessions.api_create_session';
import sessionURL from 'indico-url:sessions.api_manage_session';
import breakCreateURL from 'indico-url:timetable.tt_break_create';
import breakURL from 'indico-url:timetable.tt_break_rest';
import contributionCreateURL from 'indico-url:timetable.tt_contrib_create';
import contributionURL from 'indico-url:timetable.tt_contrib_rest';
import unscheduleContributionURL from 'indico-url:timetable.tt_contrib_unschedule';
import scheduleContribURL from 'indico-url:timetable.tt_schedule';
import sessionBlockCreateURL from 'indico-url:timetable.tt_session_block_create';
import sessionBlockURL from 'indico-url:timetable.tt_session_block_rest';

import {Moment} from 'moment';
import {Dispatch} from 'redux';
import {ThunkDispatch} from 'redux-thunk/es';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {getRandomColors, parseColorsToSchema} from './colors';
import {mapDataToEntry, mapDataToSession} from './mapperUtils';
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
  SidePanelView,
  ContribId,
  isChildEntry,
} from './types';
import {getEntryUniqueId, getEntryURLByObjId} from './utils';

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
export const DELETE_UNSCHEDULED_CONTRIB = 'Delete contrib';
export const ADD_UNSCHEDULED_CONTRIB = 'Add unscheduled contrib';
export const DELETE_BLOCK = 'Delete block';
export const SCHEDULE_ENTRY = 'Schedule entry';
export const UNSCHEDULE_ENTRY = 'Unschedule entry';
export const TOGGLE_EXPAND = 'Toggle expand';
export const TOGGLE_DRAFT = 'Toggle draft mode';
export const SET_ACTIVE_PANEL = 'Set active tab in side panel';
export const SET_EXPANDED_SESSION_BLOCK_ID = 'Set expanded session block ID';
export const CREATE_ENTRY = 'Create entry';
export const UPDATE_UNSCHEDULED_ENTRY = 'Update unscheduled entry';
export const UPDATE_ENTRY = 'Update entry';

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
  entry: Entry;
}

interface UpdateUnscheduledEntryAction {
  type: typeof UPDATE_UNSCHEDULED_ENTRY;
  id: ContribId;
  changes: Partial<ContribEntry>;
  entryType: EntryType;
}

interface UpdateEntryAction {
  type: typeof UPDATE_ENTRY;
  entry: TopLevelEntry;
  entryType: string;
  changes: Partial<Entry>;
  currentDay: string;
}

interface DeleteBreakAction {
  type: typeof DELETE_BREAK;
  entry: BlockEntry | BreakEntry | ChildBreakEntry;
}

interface DeleteBlockAction {
  type: typeof DELETE_BLOCK;
  entry: BlockEntry;
}

interface DeleteUnscheduledContribAction {
  type: typeof DELETE_UNSCHEDULED_CONTRIB;
  id: ContribId;
  eventId: number;
}

interface AddUnscheduledContribAction {
  type: typeof ADD_UNSCHEDULED_CONTRIB;
  entry: UnscheduledContribEntry;
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

interface SetActivePanelAction {
  type: typeof SET_ACTIVE_PANEL;
  panel: SidePanelView;
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

interface SetExpandedSessionBlockIdAction {
  sessionBlockId: string | null;
  type: typeof SET_EXPANDED_SESSION_BLOCK_ID;
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
  | DeleteUnscheduledContribAction
  | AddUnscheduledContribAction
  | DeleteBlockAction
  | SetDraftEntryAction
  | SetSessionDataAction
  | EditSessionAction
  | CreateSessionAction
  | DeleteSessionAction
  | SetActivePanelAction
  | SetCurrentDateAction
  | ToggleExpandAction
  | ToggleDraftAction
  | UpdateUnscheduledEntryAction
  | SetExpandedSessionBlockIdAction;

export function setTimetableData(data: any, eventInfo: any): SetTimetableDataAction {
  return {type: SET_TIMETABLE_DATA, data, eventInfo};
}

export function setSessionData(data: any): SetSessionDataAction {
  return {type: SET_SESSION_DATA, data};
}

export function editSession(sessionId: number, payload: Record<string, unknown>) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {
      staticData: {eventId},
      sessions,
    } = getState();
    const url = sessionURL({event_id: eventId, session_id: sessionId});
    const partialSession = mapDataToSession(payload, true);
    const changedSession = {...sessions[sessionId], ...partialSession};

    return dispatch(
      synchronizedAjaxAction(() => indicoAxios.patch(url, payload), {
        type: EDIT_SESSION,
        session: changedSession,
      })
    );
  };
}

// TODO: (Ajob) Implement interface for raw data session (e.g. uses ColorSchema)
export function createSession(session) {
  return async (
    dispatch: ThunkDispatch<ReduxState, unknown, Action>,
    getState: () => ReduxState
  ) => {
    const {
      staticData: {eventId},
    } = getState();
    const url = createSessionURL({event_id: eventId});

    try {
      if (!session.colors) {
        session.colors = parseColorsToSchema(getRandomColors());
      }

      const {data: newSession} = await indicoAxios.post(url, session);

      return dispatch({
        type: CREATE_SESSION,
        session: mapDataToSession(newSession),
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
    const {
      staticData,
      entries: {entries: stateEntries},
    } = getState();
    const eventId = staticData.eventId;

    const entryURL = getEntryURLByObjId(eventId, entry.type, entry.objId);

    const entryData = {
      start_dt: entry.startDt.format(),
      session_block_id: sessionBlockId,
    };

    const entryBeforeChanges = stateEntries[entry.id];
    if (
      entryBeforeChanges && // XXX can this actually be undefined?
      entryBeforeChanges.startDt.isSame(entry.startDt) &&
      entryBeforeChanges.sessionId === entry.sessionId
    ) {
      // No changes were actually made, don't update state or backend
      return;
    }

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

export function setExpandedSessionBlock(
  sessionBlockId: string | null
): SetExpandedSessionBlockIdAction {
  return {type: SET_EXPANDED_SESSION_BLOCK_ID, sessionBlockId};
}

export function resizeEntry(entry: Entry, duration: number, date: string) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {staticData} = getState();
    const eventId = staticData.eventId;
    const entryURL = getEntryURLByObjId(eventId, entry.type, entry.objId);
    const entryData = {duration: duration * 60};

    if (entry.duration === duration) {
      // No changes were actually made, don't update state or backend
      return;
    }

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

export function deleteUnscheduledContrib(id: number, eventId: number) {
  const unscheduledContribURL = contributionURL({event_id: eventId, contrib_id: id});
  return synchronizedAjaxAction(() => indicoAxios.delete(unscheduledContribURL), {
    type: DELETE_UNSCHEDULED_CONTRIB,
    id: getEntryUniqueId(EntryType.Contribution, id) as ContribId,
    eventId,
  });
}

export function addUnscheduledContrib(entry: UnscheduledContribEntry) {
  return {
    type: ADD_UNSCHEDULED_CONTRIB,
    entry,
  };
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
  entry: ContribEntry | ChildContribEntry,
  layoutOverrides
) {
  const scheduleURL = scheduleContribURL(
    isChildEntry(entry)
      ? {event_id: eventId, block_id: entry.sessionBlockId?.slice(1)}
      : {event_id: eventId}
  );
  // TODO only pass contribId and none of the other stuff here?!
  return synchronizedAjaxAction(
    () =>
      indicoAxios.post(scheduleURL, {
        contribs: [{contrib_id: entry.objId, start_dt: entry.startDt.toISOString()}],
      }),
    {
      type: SCHEDULE_ENTRY,
      entry,
      layoutOverrides,
    }
  );
}

export function unscheduleEntry(entry: ContribEntry, eventId: number) {
  const entryURL = unscheduleContributionURL({event_id: eventId, contrib_id: entry.objId});
  return synchronizedAjaxAction(() => indicoAxios.post(entryURL), {
    type: UNSCHEDULE_ENTRY,
    entry,
  });
}

export function setActivePanel(panel: SidePanelView) {
  return {
    type: SET_ACTIVE_PANEL,
    panel,
  };
}

function _createEntry(entryType: EntryType, entry: Entry): CreateEntryAction {
  return {type: CREATE_ENTRY, entryType, entry};
}

export function createEntry(entryType: EntryType, payload: any) {
  return async (
    dispatch: ThunkDispatch<ReduxState, unknown, Action>,
    getState: () => ReduxState
  ) => {
    const {
      staticData: {eventId},
    } = getState();
    const createURL = {
      [EntryType.Contribution]: contributionCreateURL({event_id: eventId}),
      [EntryType.SessionBlock]: sessionBlockCreateURL({event_id: eventId}),
      [EntryType.Break]: breakCreateURL({event_id: eventId}),
    }[entryType];

    const data = (await indicoAxios.post(createURL, payload))?.data;
    data.type = entryType;
    const resEntry = mapDataToEntry(data);
    return dispatch(_createEntry(resEntry.type, resEntry as Entry));
  };
}

export function updateUnscheduledEntry(
  entryType: EntryType, // In preperation for potentially using other draft types
  id: ContribId,
  changes: Partial<ContribEntry>
): UpdateUnscheduledEntryAction {
  return {type: UPDATE_UNSCHEDULED_ENTRY, entryType, id, changes};
}

export function _updateEntry(
  entryType: EntryType,
  entry: Entry,
  currentDay: string,
  changes: Partial<Entry>
): UpdateEntryAction {
  return {type: UPDATE_ENTRY, entryType, entry, currentDay, changes};
}

export function updateEntry(
  entryType: EntryType,
  entry: Entry,
  currentDay: string,
  customPayload: any
) {
  return (dispatch: ThunkDispatch<ReduxState, unknown, Action>, getState: () => ReduxState) => {
    const {
      staticData: {eventId},
    } = getState();
    const updateURL = {
      [EntryType.Contribution]: contributionURL({event_id: eventId, contrib_id: entry.objId}),
      [EntryType.SessionBlock]: sessionBlockURL({event_id: eventId, session_block_id: entry.objId}),
      [EntryType.Break]: breakURL({event_id: eventId, break_id: entry.objId}),
    }[entryType];

    const action = synchronizedAjaxAction(
      () => indicoAxios.patch(updateURL, customPayload),
      _updateEntry(entryType, entry, currentDay, mapDataToEntry(customPayload))
    );
    return dispatch(action);
  };
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
