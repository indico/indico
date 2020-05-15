// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createBookingURL from 'indico-url:rb.create_booking';
import fetchTimelineURL from 'indico-url:rb.timeline';
import fetchSuggestionsURL from 'indico-url:rb.suggestions';
import searchRoomsURL from 'indico-url:rb.search_rooms';
import fetchEventsURL from 'indico-url:rb.events';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';
import {ajax as ajaxRules} from './serializers';
import {validateFilters} from '../../common/filters';
import {preProcessParameters} from '../../util';
import {actions as modalActions} from '../../modals';

import {roomSearchActionsFactory} from '../../common/roomSearch/actions';
import {ajax as ajaxFilterRules} from '../../common/roomSearch/serializers';
import {selectors as userSelectors} from '../../common/user';

// Booking creation
export const CREATE_BOOKING_REQUEST = 'bookRoom/CREATE_BOOKING_REQUEST';
export const CREATE_BOOKING_SUCCESS = 'bookRoom/CREATE_BOOKING_SUCCESS';
export const CREATE_BOOKING_FAILED = 'bookRoom/CREATE_BOOKING_FAILED';

// Checking availability of room
export const GET_BOOKING_AVAILABILITY_REQUEST = 'bookRoom/GET_BOOKING_AVAILABILITY_REQUEST';
export const GET_BOOKING_AVAILABILITY_SUCCESS = 'bookRoom/GET_BOOKING_AVAILABILITY_SUCCESS';
export const GET_BOOKING_AVAILABILITY_ERROR = 'bookRoom/GET_BOOKING_AVAILABILITY_ERROR';
export const RESET_BOOKING_AVAILABILITY = 'bookRoom/RESET_BOOKING_AVAILABILITY';
export const SET_BOOKING_AVAILABILITY = 'bookRoom/SET_BOOKING_AVAILABILITY';

// Timeline
export const TOGGLE_TIMELINE_VIEW = 'bookRoom/TOGGLE_TIMELINE_VIEW';
export const INIT_TIMELINE = 'bookRoom/INIT_TIMELINE';
export const ADD_TIMELINE_ROOMS = 'bookRoom/ADD_TIMELINE_ROOMS';
export const GET_TIMELINE_REQUEST = 'bookRoom/GET_TIMELINE_REQUEST';
export const GET_TIMELINE_SUCCESS = 'bookRoom/GET_TIMELINE_SUCCESS';
export const GET_TIMELINE_ERROR = 'bookRoom/GET_TIMELINE_ERROR';
export const TIMELINE_RECEIVED = 'bookRoom/TIMELINE_RECEIVED';
export const SET_TIMELINE_MODE = 'bookRoom/SET_TIMELINE_MODE';
export const SET_TIMELINE_DATE = 'bookRoom/SET_TIMELINE_DATE';

// Unavailable room list
export const GET_UNAVAILABLE_TIMELINE_REQUEST = 'bookRoom/GET_UNAVAILABLE_TIMELINE_REQUEST';
export const GET_UNAVAILABLE_TIMELINE_SUCCESS = 'bookRoom/GET_UNAVAILABLE_TIMELINE_SUCCESS';
export const GET_UNAVAILABLE_TIMELINE_ERROR = 'bookRoom/GET_UNAVAILABLE_TIMELINE_ERROR';
export const UNAVAILABLE_TIMELINE_RECEIVED = 'bookRoom/UNAVAILABLE_TIMELINE_RECEIVED';
export const SET_UNAVAILABLE_NAV_MODE = 'bookRoom/SET_UNAVAILABLE_NAV_MODE';
export const SET_UNAVAILABLE_NAV_DATE = 'bookRoom/SET_UNAVAILABLE_NAV_DATE';
export const INIT_UNAVAILABLE_TIMELINE = 'bookRoom/INIT_UNAVAILABLE_TIMELINE';

// Suggestions
export const FETCH_SUGGESTIONS_REQUEST = 'bookRoom/FETCH_SUGGESTIONS_REQUEST';
export const FETCH_SUGGESTIONS_SUCCESS = 'bookRoom/FETCH_SUGGESTIONS_SUCCESS';
export const FETCH_SUGGESTIONS_ERROR = 'bookRoom/FETCH_SUGGESTIONS_ERROR';
export const SUGGESTIONS_RECEIVED = 'bookRoom/SUGGESTIONS_RECEIVED';
export const RESET_SUGGESTIONS = 'bookRoom/RESET_SUGGESTIONS';

// Related events
export const FETCH_RELATED_EVENTS_REQUEST = 'bookRoom/FETCH_RELATED_EVENTS_REQUEST';
export const FETCH_RELATED_EVENTS_SUCCESS = 'bookRoom/FETCH_RELATED_EVENTS_SUCCESS';
export const FETCH_RELATED_EVENTS_ERROR = 'bookRoom/FETCH_RELATED_EVENTS_ERROR';
export const RELATED_EVENTS_RECEIVED = 'bookRoom/RELATED_EVENTS_RECEIVED';
export const RESET_RELATED_EVENTS = 'bookRoom/RESET_RELATED_EVENTS';

export function createBooking(args, isAdminOverrideEnabled) {
  const params = preProcessParameters(args, ajaxRules);
  if (isAdminOverrideEnabled) {
    params.admin_override_enabled = true;
  }
  return submitFormAction(
    () => indicoAxios.post(createBookingURL(), params),
    CREATE_BOOKING_REQUEST,
    CREATE_BOOKING_SUCCESS,
    CREATE_BOOKING_FAILED
  );
}

export function resetBookingAvailability() {
  return {type: RESET_BOOKING_AVAILABILITY};
}

export function fetchBookingAvailability(room, filters) {
  return async (dispatch, getStore) => {
    const store = getStore();
    const {dates, timeSlot, recurrence} = filters;
    const params = preProcessParameters({dates, timeSlot, recurrence}, ajaxFilterRules);
    if (userSelectors.isUserAdminOverrideEnabled(store)) {
      params.admin_override_enabled = true;
    }
    return await ajaxAction(
      () => indicoAxios.get(fetchTimelineURL({room_id: room.id}), {params}),
      GET_BOOKING_AVAILABILITY_REQUEST,
      [SET_BOOKING_AVAILABILITY, GET_BOOKING_AVAILABILITY_SUCCESS],
      GET_BOOKING_AVAILABILITY_ERROR
    )(dispatch);
  };
}

export function fetchUnavailableRooms(filters) {
  return async (dispatch, getStore) => {
    dispatch({type: GET_UNAVAILABLE_TIMELINE_REQUEST});
    const store = getStore();
    const isAdminOverrideEnabled = userSelectors.isUserAdminOverrideEnabled(store);
    const searchParams = preProcessParameters(filters, ajaxFilterRules);
    searchParams.unavailable = true;
    if (isAdminOverrideEnabled) {
      searchParams.admin_override_enabled = true;
    }

    let response;
    try {
      response = await indicoAxios.get(searchRoomsURL(), {params: searchParams});
    } catch (error) {
      const message = handleAxiosError(error);
      dispatch({type: GET_UNAVAILABLE_TIMELINE_ERROR, error: message});
      return;
    }

    const roomIds = response.data.rooms;
    const {dates, timeSlot, recurrence} = filters;
    const timelineParams = preProcessParameters({dates, timeSlot, recurrence}, ajaxFilterRules);
    if (isAdminOverrideEnabled) {
      timelineParams.admin_override_enabled = true;
    }
    return await ajaxAction(
      () => indicoAxios.post(fetchTimelineURL(), {room_ids: roomIds}, {params: timelineParams}),
      null,
      [UNAVAILABLE_TIMELINE_RECEIVED, GET_UNAVAILABLE_TIMELINE_SUCCESS],
      GET_UNAVAILABLE_TIMELINE_ERROR
    )(dispatch);
  };
}

export function initTimeline(roomIds, dates, timeSlot, recurrence) {
  return {
    type: INIT_TIMELINE,
    params: {dates, timeSlot, recurrence},
    roomIds,
  };
}

export function addTimelineRooms(roomIds) {
  return {
    type: ADD_TIMELINE_ROOMS,
    roomIds,
  };
}

export function fetchTimeline() {
  const PER_PAGE = 20;

  return async (dispatch, getStore) => {
    const store = getStore();
    const {
      bookRoom: {
        timeline: {
          data: {params: stateParams, roomIds: stateRoomIds, availability: stateAvailability},
        },
      },
    } = store;
    const params = preProcessParameters(stateParams, ajaxFilterRules);
    if (userSelectors.isUserAdminOverrideEnabled(store)) {
      params.admin_override_enabled = true;
    }
    const numFetchedIds = stateAvailability.length;
    const roomIds = stateRoomIds.slice(numFetchedIds, numFetchedIds + PER_PAGE);
    if (!roomIds.length) {
      console.warn('Tried to fetch timeline for zero rooms');
      return Promise.reject();
    }

    return await ajaxAction(
      () => indicoAxios.post(fetchTimelineURL(), {room_ids: roomIds}, {params}),
      GET_TIMELINE_REQUEST,
      [TIMELINE_RECEIVED, GET_TIMELINE_SUCCESS],
      GET_TIMELINE_ERROR
    )(dispatch);
  };
}

export function toggleTimelineView(visible) {
  return {type: TOGGLE_TIMELINE_VIEW, visible};
}

export function fetchRoomSuggestions() {
  return async (dispatch, getStore) => {
    const {
      bookRoom: {filters},
    } = getStore();
    if (!validateFilters(filters, 'bookRoom', dispatch)) {
      return;
    }
    const params = preProcessParameters(filters, ajaxFilterRules);

    return await ajaxAction(
      () => indicoAxios.get(fetchSuggestionsURL(), {params}),
      FETCH_SUGGESTIONS_REQUEST,
      [SUGGESTIONS_RECEIVED, FETCH_SUGGESTIONS_SUCCESS],
      FETCH_SUGGESTIONS_ERROR
    )(dispatch);
  };
}

export function resetRoomSuggestions() {
  return {type: RESET_SUGGESTIONS};
}

export const {searchRooms} = roomSearchActionsFactory('bookRoom');

export const openBookRoom = (roomId, data = null) =>
  modalActions.openModal('book-room', roomId, data);
export const openUnavailableRooms = () => modalActions.openModal('unavailable-rooms');
export const openBookingForm = (roomId, data) =>
  modalActions.openModal('booking-form', roomId, data);
export function setTimelineDate(date) {
  return {type: SET_TIMELINE_DATE, date};
}

export function setTimelineMode(mode) {
  return {type: SET_TIMELINE_MODE, mode};
}

export function setUnavailableNavDate(date) {
  return {type: SET_UNAVAILABLE_NAV_DATE, date};
}

export function setUnavailableNavMode(mode) {
  return {type: SET_UNAVAILABLE_NAV_MODE, mode};
}

export function initUnavailableTimeline(selectedDate, mode) {
  return {type: INIT_UNAVAILABLE_TIMELINE, selectedDate, mode};
}

export function fetchRelatedEvents(filters) {
  const {dates, timeSlot, recurrence} = filters;
  const params = preProcessParameters({dates, timeSlot, recurrence}, ajaxFilterRules);
  return ajaxAction(
    () => indicoAxios.get(fetchEventsURL(), {params}),
    FETCH_RELATED_EVENTS_REQUEST,
    [RELATED_EVENTS_RECEIVED, FETCH_RELATED_EVENTS_SUCCESS],
    FETCH_RELATED_EVENTS_ERROR
  );
}

export function resetRelatedEvents() {
  return {type: RESET_RELATED_EVENTS};
}
