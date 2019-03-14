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

import favoriteUsersURL from 'indico-url:users.favorites_api';
import principalsURL from 'indico-url:core.principals';

import _ from 'lodash';
import {useEffect, useState} from 'react';
import {handleAxiosError, indicoAxios} from '../utils/axios';
import {camelizeKeys} from '../utils/case';


/**
 * Helper to use async functions with useEffect as the function that is
 * passed to useEffect must not return anything except a cleanup function,
 * so passing async functions directly is not allowed.
 *
 * Using this hook, there is obviously no way to return a cleanup function,
 * but this should be used for simple AJAX calls where no cleanup is needed.
 */
export const useAsyncEffect = (fn, ...args) => {
    useEffect(() => {
        fn();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, ...args);
};


export const useFavoriteUsers = () => {
    // XXX: this state should ideally be global so if this hook is used more than
    // once on the same page we keep the favorites in sync and don't send multiple
    // requests to load the initial list
    const [favorites, setFavorites] = useState({});

    const apiCall = async (method, id = null, source = null) => {
        let response;
        try {
            response = await indicoAxios.request({
                method,
                url: favoriteUsersURL(id !== null ? {user_id: id} : {}),
                cancelToken: source ? source.token : null,
            });
        } catch (error) {
            handleAxiosError(error);
            return null;
        }
        return response.data;
    };

    const fetchDetails = async (ids, source = null) => {
        const values = ids.map(id => `User:${id}`);
        let response;
        try {
            response = await indicoAxios.post(principalsURL(), {values}, {cancelToken: source ? source.token : null});
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        return _.fromPairs(Object.values(camelizeKeys(response.data)).map(x => [x.userId, x]));
    };

    const del = async (id) => {
        if (await apiCall('DELETE', id) !== null) {
            setFavorites(values => _.omit(values, id));
        }
    };

    const add = async (id) => {
        if (await apiCall('PUT', id) !== null) {
            const data = await fetchDetails([id]);
            if (data !== null) {
                setFavorites(values => ({...values, ...data}));
            }
        }
    };

    useEffect(() => {
        const source = indicoAxios.CancelToken.source();

        (async () => {
            const ids = await apiCall('GET', null, source);
            if (ids === null || !ids.length) {
                return;
            }
            const data = await fetchDetails(ids, source);
            setFavorites(data);
        })();

        return () => {
            source.cancel();
        };
    }, []);

    return [favorites, [add, del]];
};
