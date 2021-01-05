// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fetchActiveBookingsURL from 'indico-url:rb.active_bookings';
import fetchCalendarURL from 'indico-url:rb.calendar';
import searchRoomsURL from 'indico-url:rb.search_rooms';

import _ from 'lodash';
import moment from 'moment';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

import {ajaxRules as roomSearchAjaxRules} from '../../common/roomSearch';
import {selectors as userSelectors} from '../../common/user';
import {preProcessParameters} from '../../util';

import {getRoomFilters, getCalendarFilters} from './selectors';
import {ajax as ajaxRules} from './serializers';

export const CHANGE_VIEW = 'calendar/CHANGE_VIEW';
export const SET_DATE = 'calendar/SET_DATE';
export const SET_MODE = 'calendar/SET_MODE';
export const ROWS_RECEIVED = 'calendar/ROWS_RECEIVED';
export const FETCH_CALENDAR_REQUEST = 'calendar/FETCH_CALENDAR_REQUEST';
export const FETCH_CALENDAR_SUCCESS = 'calendar/FETCH_CALENDAR_SUCCESS';
export const FETCH_CALENDAR_ERROR = 'calendar/FETCH_CALENDAR_ERROR';
export const ROOM_IDS_RECEIVED = 'calendar/ROOM_IDS_RECEIVED';

export const FETCH_ACTIVE_BOOKINGS_REQUEST = 'calendar/FETCH_ACTIVE_BOOKINGS_REQUEST';
export const FETCH_ACTIVE_BOOKINGS_SUCCESS = 'calendar/FETCH_ACTIVE_BOOKINGS_SUCCESS';
export const FETCH_ACTIVE_BOOKINGS_ERROR = 'calendar/FETCH_ACTIVE_BOOKINGS_ERROR';
export const ACTIVE_BOOKINGS_RECEIVED = 'calendar/ACTIVE_BOOKINGS_RECEIVED';
export const CLEAR_ACTIVE_BOOKINGS = 'calendar/CLEAR_ACTIVE_BOOKINGS';

export function changeView(view) {
  return {type: CHANGE_VIEW, view};
}

export function setDate(date) {
  return {type: SET_DATE, date};
}

export function setMode(mode) {
  return {type: SET_MODE, mode};
}

async function fetchCalendarRooms(dispatch, state) {
  const roomFilters = getRoomFilters(state);
  const searchParams = preProcessParameters({...roomFilters}, roomSearchAjaxRules);

  if (userSelectors.isUserAdminOverrideEnabled(state)) {
    searchParams.is_admin = true;
  }

  let response;

  try {
    response = await indicoAxios.get(searchRoomsURL(), {params: searchParams});
  } catch (error) {
    const message = handleAxiosError(error);
    dispatch({type: FETCH_CALENDAR_ERROR, error: message});
    return [];
  }

  const newRoomIds = response.data.rooms;
  dispatch({type: ROOM_IDS_RECEIVED, data: newRoomIds});
  if (!newRoomIds.length) {
    dispatch({type: ROWS_RECEIVED, data: []});
  }

  return newRoomIds;
}

export function fetchCalendar(fetchRooms = true) {
  return async (dispatch, getState) => {
    dispatch({type: FETCH_CALENDAR_REQUEST});

    const state = getState();
    const {myBookings, showInactive} = getCalendarFilters(state);
    const {text} = getRoomFilters(state);
    const {
      data: {roomIds},
      datePicker,
    } = state.calendar;
    let newRoomIds = roomIds;

    if (fetchRooms) {
      newRoomIds = await fetchCalendarRooms(dispatch, state);
      if (!text && !newRoomIds.length) {
        dispatch({
          type: FETCH_CALENDAR_SUCCESS,
        });
        return;
      }
    }

    const params = preProcessParameters({...datePicker, myBookings, showInactive, text}, ajaxRules);
    return await ajaxAction(
      () => indicoAxios.post(fetchCalendarURL(), {room_ids: newRoomIds}, {params}),
      null,
      [ROWS_RECEIVED, FETCH_CALENDAR_SUCCESS],
      [FETCH_CALENDAR_ERROR]
    )(dispatch);
  };
}

export function fetchActiveBookings(limit, fetchRooms = true) {
  return async (dispatch, getState) => {
    dispatch({type: FETCH_ACTIVE_BOOKINGS_REQUEST});

    const state = getState();
    const {myBookings} = getCalendarFilters(state);
    const {text} = getRoomFilters(state);
    const {
      data: {roomIds},
      activeBookings: {data},
    } = state.calendar;
    let newRoomIds = roomIds;

    if (fetchRooms) {
      newRoomIds = await fetchCalendarRooms(dispatch, state);
      if (!text && !newRoomIds.length) {
        dispatch({type: FETCH_ACTIVE_BOOKINGS_SUCCESS});
        return;
      }
    }

    const params = preProcessParameters({myBookings, text}, ajaxRules);
    const body = {room_ids: newRoomIds, limit};

    if (Object.keys(data).length) {
      const lastDt = Object.keys(data).reverse()[0];
      body.start_dt = _.maxBy(data[lastDt], rv =>
        moment(rv.startDt, 'YYYY-MM-DD HH:mm').unix()
      ).startDt;
      body.last_reservation_id = data[lastDt][data[lastDt].length - 1].reservation.id;
    }

    return await ajaxAction(
      () => indicoAxios.post(fetchActiveBookingsURL(), body, {params}),
      null,
      [ACTIVE_BOOKINGS_RECEIVED, FETCH_ACTIVE_BOOKINGS_SUCCESS],
      [FETCH_ACTIVE_BOOKINGS_ERROR]
    )(dispatch);
  };
}

export function clearActiveBookings() {
  return {type: CLEAR_ACTIVE_BOOKINGS};
}
