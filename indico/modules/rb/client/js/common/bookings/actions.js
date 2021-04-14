// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fetchBookingDetailsURL from 'indico-url:rb.booking_details';
import bookingOccurrenceStateActionsURL from 'indico-url:rb.booking_occurrence_state_actions';
import bookingStateActionsURL from 'indico-url:rb.booking_state_actions';
import bookingDeleteURL from 'indico-url:rb.delete_booking';
import bookingUpdateURL from 'indico-url:rb.update_booking';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';

import {openModal} from '../../actions';

export const BOOKING_DETAILS_RECEIVED = 'bookings/BOOKING_DETAILS_RECEIVED';
export const FETCH_BOOKING_DETAILS_REQUEST = 'bookings/FETCH_BOOKING_DETAILS_REQUEST';
export const FETCH_BOOKING_DETAILS_SUCCESS = 'bookings/FETCH_BOOKING_DETAILS_SUCCESS';
export const FETCH_BOOKING_DETAILS_ERROR = 'bookings/FETCH_BOOKING_DETAILS_ERROR';

export const BOOKING_STATE_CHANGE_REQUEST = 'bookings/BOOKING_STATE_CHANGE_REQUEST';
export const BOOKING_STATE_CHANGE_SUCCESS = 'bookings/BOOKING_STATE_CHANGE_SUCCESS';
export const BOOKING_STATE_CHANGE_ERROR = 'bookings/BOOKING_STATE_CHANGE_ERROR';
export const BOOKING_STATE_UPDATED = 'bookings/BOOKING_STATE_UPDATED';

export const DELETE_BOOKING_REQUEST = 'bookings/DELETE_BOOKING_REQUEST';
export const DELETE_BOOKING_SUCCESS = 'bookings/DELETE_BOOKING_SUCCESS';
export const DELETE_BOOKING_ERROR = 'bookings/DELETE_BOOKING_ERROR';

export const UPDATE_BOOKING_REQUEST = 'bookings/UPDATE_BOOKING_REQUEST';
export const UPDATE_BOOKING_SUCCESS = 'bookings/UPDATE_BOOKING_SUCCESS';
export const UPDATE_BOOKING_ERROR = 'bookings/UPDATE_BOOKING_ERROR';
export const UPDATED_BOOKING_RECEIVED = 'bookings/UPDATED_BOOKING_RECEIVED';

export const BOOKING_OCCURRENCE_STATE_CHANGE_REQUEST =
  'bookings/BOOKING_OCCURRENCE_STATE_CHANGE_REQUEST';
export const BOOKING_OCCURRENCE_STATE_CHANGE_SUCCESS =
  'bookings/BOOKING_OCCURRENCE_STATE_CHANGE_SUCCESS';
export const BOOKING_OCCURRENCE_STATE_CHANGE_ERROR =
  'bookings/BOOKING_OCCURRENCE_STATE_CHANGE_ERROR';
export const BOOKING_OCCURRENCE_STATE_UPDATED = 'bookings/BOOKING_OCCURRENCE_STATE_UPDATED';

export function fetchBookingDetails(id) {
  return ajaxAction(
    () => indicoAxios.get(fetchBookingDetailsURL({booking_id: id})),
    FETCH_BOOKING_DETAILS_REQUEST,
    [BOOKING_DETAILS_RECEIVED, FETCH_BOOKING_DETAILS_SUCCESS],
    FETCH_BOOKING_DETAILS_ERROR
  );
}

export const openBookingDetails = bookingId => openModal('booking-details', bookingId);

export function changeBookingState(id, action, params = {}) {
  return ajaxAction(
    () => indicoAxios.post(bookingStateActionsURL({booking_id: id, action}), params),
    BOOKING_STATE_CHANGE_REQUEST,
    [BOOKING_STATE_UPDATED, BOOKING_STATE_CHANGE_SUCCESS],
    BOOKING_STATE_CHANGE_ERROR
  );
}

export function deleteBooking(id) {
  return ajaxAction(
    () => indicoAxios.delete(bookingDeleteURL({booking_id: id})),
    DELETE_BOOKING_REQUEST,
    DELETE_BOOKING_SUCCESS,
    DELETE_BOOKING_ERROR
  );
}

export function updateBooking(id, params) {
  return submitFormAction(
    () => indicoAxios.patch(bookingUpdateURL({booking_id: id}), params),
    UPDATE_BOOKING_REQUEST,
    [UPDATE_BOOKING_SUCCESS, UPDATED_BOOKING_RECEIVED],
    UPDATE_BOOKING_ERROR,
    {booking_reason: 'reason'}
  );
}

export function changeBookingOccurrenceState(id, date, action, params = {}) {
  return ajaxAction(
    () =>
      indicoAxios.post(bookingOccurrenceStateActionsURL({booking_id: id, date, action}), params),
    BOOKING_OCCURRENCE_STATE_CHANGE_REQUEST,
    [BOOKING_OCCURRENCE_STATE_UPDATED, BOOKING_OCCURRENCE_STATE_CHANGE_SUCCESS],
    BOOKING_OCCURRENCE_STATE_CHANGE_ERROR
  );
}
