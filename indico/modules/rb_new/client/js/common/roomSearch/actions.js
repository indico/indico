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

import searchRoomsURL from 'indico-url:rooms_new.search_rooms';
import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction} from 'indico/utils/redux';
import {preProcessParameters} from '../../util';
import {ajax as ajaxFilterRules} from './serializers';
import {validateFilters} from '../filters';
import {selectors as userSelectors} from '../../common/user';


export function roomSearchActionsFactory(namespace) {
    const SEARCH_RESULTS_RECEIVED = `${namespace}/SEARCH_RESULTS_RECEIVED`;
    const SEARCH_ROOMS_REQUEST = `${namespace}/SEARCH_ROOMS_REQUEST`;
    const SEARCH_ROOMS_SUCCESS = `${namespace}/SEARCH_ROOMS_SUCCESS`;
    const SEARCH_ROOMS_ERROR = `${namespace}/SEARCH_ROOMS_ERROR`;

    function searchRooms() {
        return async (dispatch, getStore) => {
            const {[namespace]: {filters}} = getStore();
            if (!validateFilters(filters, namespace, dispatch)) {
                return;
            }
            const isAdmin = userSelectors.isUserAdminOverrideEnabled(getStore());
            const params = preProcessParameters(filters, ajaxFilterRules);
            params.is_admin = isAdmin;
            return await ajaxAction(
                () => indicoAxios.get(searchRoomsURL(), {params}),
                SEARCH_ROOMS_REQUEST,
                [SEARCH_RESULTS_RECEIVED, SEARCH_ROOMS_SUCCESS],
                SEARCH_ROOMS_ERROR
            )(dispatch);
        };
    }

    return {
        SEARCH_RESULTS_RECEIVED,
        SEARCH_ROOMS_REQUEST,
        SEARCH_ROOMS_SUCCESS,
        SEARCH_ROOMS_ERROR,
        searchRooms,
    };
}
