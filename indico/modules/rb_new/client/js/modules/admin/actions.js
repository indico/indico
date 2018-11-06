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

import fetchLocationsURL from 'indico-url:rooms_new.admin_locations';

import {ajaxAction} from 'indico/utils/redux';
import {indicoAxios} from 'indico/utils/axios';
import {actions as filtersActions} from '../../common/filters';


export const FETCH_LOCATIONS_REQUEST = 'admin/FETCH_LOCATIONS_REQUEST';
export const FETCH_LOCATIONS_SUCCESS = 'admin/FETCH_LOCATIONS_SUCCESS';
export const FETCH_LOCATIONS_ERROR = 'admin/FETCH_LOCATIONS_ERROR';
export const LOCATIONS_RECEIVED = 'admin/LOCATIONS_RECEIVED';

export const FILTER_NAMESPACE = 'admin';


export function fetchLocations() {
    return ajaxAction(
        () => indicoAxios.get(fetchLocationsURL()),
        FETCH_LOCATIONS_REQUEST,
        [LOCATIONS_RECEIVED, FETCH_LOCATIONS_SUCCESS],
        FETCH_LOCATIONS_ERROR
    );
}

export function clearTextFilter() {
    return filtersActions.setFilterParameter(FILTER_NAMESPACE, 'text', null);
}
