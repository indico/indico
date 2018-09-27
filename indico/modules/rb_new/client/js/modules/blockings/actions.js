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

import fetchBlockingsURL from 'indico-url:rooms_new.blockings';
import createBlockingURL from 'indico-url:rooms_new.create_blocking';
import updateBlockingURL from 'indico-url:rooms_new.update_blocking';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';
import {preProcessParameters} from '../../util';
import {ajax as ajaxRules} from './serializers';
import {actions as filtersActions} from '../../common/filters';


export const FETCH_BLOCKINGS_REQUEST = 'blockings/FETCH_BLOCKINGS_REQUEST';
export const FETCH_BLOCKINGS_SUCCESS = 'blockings/FETCH_BLOCKINGS_SUCCESS';
export const FETCH_BLOCKINGS_ERROR = 'blockings/FETCH_BLOCKINGS_ERROR';
export const BLOCKINGS_RECEIVED = 'blockings/BLOCKINGS_RECEIVED';

export const CREATE_BLOCKING_REQUEST = 'blockings/CREATE_BLOCKING_REQUEST';
export const CREATE_BLOCKING_SUCCESS = 'blockings/CREATE_BLOCKING_SUCCESS';
export const CREATE_BLOCKING_ERROR = 'blockings/CREATE_BLOCKING_ERROR';

export const UPDATE_BLOCKING_REQUEST = 'blockings/UPDATE_BLOCKING_REQUEST';
export const UPDATE_BLOCKING_SUCCESS = 'blockings/UPDATE_BLOCKING_SUCCESS';
export const UPDATE_BLOCKING_ERROR = 'blockings/UPDATE_BLOCKING_ERROR';

export const FILTER_NAMESPACE = 'blockings';


export function fetchBlockings() {
    return async (dispatch, getStore) => {
        const {blockings: {filters}} = getStore();
        const params = preProcessParameters(filters, ajaxRules);
        return await ajaxAction(
            () => indicoAxios.get(fetchBlockingsURL(), {params}),
            FETCH_BLOCKINGS_REQUEST,
            [BLOCKINGS_RECEIVED, FETCH_BLOCKINGS_SUCCESS],
            FETCH_BLOCKINGS_ERROR
        )(dispatch);
    };
}

export function setFilterParameter(param, value) {
    return filtersActions.setFilterParameter(FILTER_NAMESPACE, param, value);
}

export function createBlocking(formData) {
    const data = preProcessParameters(formData, ajaxRules);
    return submitFormAction(
        () => indicoAxios.post(createBlockingURL(), data),
        CREATE_BLOCKING_REQUEST, CREATE_BLOCKING_SUCCESS, CREATE_BLOCKING_ERROR
    );
}

export function updateBlocking(blockingId, formData) {
    const data = preProcessParameters(formData, ajaxRules);
    return submitFormAction(
        () => indicoAxios.patch(updateBlockingURL({blocking_id: blockingId}), data),
        UPDATE_BLOCKING_REQUEST, UPDATE_BLOCKING_SUCCESS, UPDATE_BLOCKING_ERROR
    );
}

export function updateBlockingsList(blockings) {
    return {type: BLOCKINGS_RECEIVED, data: blockings};
}
