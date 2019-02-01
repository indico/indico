/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

import getLinkedObjectDataURL from 'indico-url:rooms_new.linked_object_data';

import _ from 'lodash';
import qs from 'qs';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';


export const SET_OBJECT = 'linking/SET_OBJECT';
export const CLEAR_OBJECT = 'linking/CLEAR_OBJECT';


export function setObjectFromURL(queryString) {
    return async (dispatch) => {
        const {linkType, linkId} = qs.parse(queryString);
        if (linkType === undefined || linkId === undefined) {
            return;
        }

        let response;
        try {
            response = await indicoAxios.get(getLinkedObjectDataURL({type: _.snakeCase(linkType), id: linkId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        const data = camelizeKeys(response.data);
        if (!data.canAccess) {
            return;
        }
        dispatch({
            type: SET_OBJECT,
            objectType: linkType,
            objectId: +linkId,
            objectTitle: data.title,
            eventURL: data.eventUrl,
            eventTitle: data.eventTitle,
        });
    };
}


export function clearObject() {
    return {type: CLEAR_OBJECT};
}
