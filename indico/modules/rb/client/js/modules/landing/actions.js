// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fetchUpcomingBookingsURL from 'indico-url:rb.my_bookings';
import fetchStatsURL from 'indico-url:rb.stats';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';

export const STATS_RECEIVED = 'landing/STATS_RECEIVED';
export const FETCH_STATS_REQUEST = 'landing/FETCH_STATS_REQUEST';
export const FETCH_STATS_SUCCESS = 'landing/FETCH_STATS_SUCCESS';
export const FETCH_STATS_ERROR = 'landing/FETCH_STATS_ERROR';

export const BOOKINGS_RECEIVED = 'landing/BOOKINGS_RECEIVED';
export const FETCH_BOOKINGS_REQUEST = 'landing/FETCH_BOOKINGS_REQUEST';
export const FETCH_BOOKINGS_SUCCESS = 'landing/FETCH_BOOKINGS_SUCCESS';
export const FETCH_BOOKINGS_ERROR = 'landing/FETCH_BOOKINGS_ERROR';

export function fetchStatistics() {
  return ajaxAction(
    () => indicoAxios.get(fetchStatsURL()),
    FETCH_STATS_REQUEST,
    [STATS_RECEIVED, FETCH_STATS_SUCCESS],
    FETCH_STATS_ERROR
  );
}

export function fetchUpcomingBookings() {
  return ajaxAction(
    () => indicoAxios.get(fetchUpcomingBookingsURL()),
    FETCH_BOOKINGS_REQUEST,
    [BOOKINGS_RECEIVED, FETCH_BOOKINGS_SUCCESS],
    FETCH_BOOKINGS_ERROR
  );
}
