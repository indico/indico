/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import fetchStatsURL from 'indico-url:rooms_new.stats';
import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';


export const STATS_RECEIVED = 'landing/STATS_RECEIVED';
export const FETCH_STATS_REQUEST = 'landing/FETCH_STATS_REQUEST';
export const FETCH_STATS_SUCCESS = 'landing/FETCH_STATS_SUCCESS';
export const FETCH_STATS_ERROR = 'landing/FETCH_STATS_ERROR';


export function fetchStatistics() {
    return ajaxAction(
        () => indicoAxios.get(fetchStatsURL()),
        FETCH_STATS_REQUEST,
        [STATS_RECEIVED, FETCH_STATS_SUCCESS],
        FETCH_STATS_ERROR
    );
}
