// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import favoriteUsersURL from 'indico-url:users.favorites_api';
import principalsURL from 'indico-url:core.principals';

import _ from 'lodash';
import {useEffect, useRef, useState} from 'react';
import PropTypes from 'prop-types';
import useAxios from '@use-hooks/axios';
import {handleAxiosError, indicoAxios} from '../utils/axios';
import {camelizeKeys} from '../utils/case';

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
      response = await indicoAxios.post(
        principalsURL(),
        {values},
        {cancelToken: source ? source.token : null}
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    return _.fromPairs(Object.values(camelizeKeys(response.data)).map(x => [x.userId, x]));
  };

  const del = async id => {
    if ((await apiCall('DELETE', id)) !== null) {
      setFavorites(values => _.omit(values, id));
    }
  };

  const add = async id => {
    if ((await apiCall('PUT', id)) !== null) {
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

/**
 * FavoritesProvider can be used to get the favorite controller
 * in a class-based component.
 *
 * Do not use this for new components; write them as functional
 * components instead!
 */
export const FavoritesProvider = ({children}) => {
  const favoriteUsersController = useFavoriteUsers();
  return children(favoriteUsersController);
};

FavoritesProvider.propTypes = {
  children: PropTypes.func.isRequired,
};

export function useIndicoAxios({camelize, ...args}) {
  const lastData = useRef(null);
  const {response, error, loading, reFetch} = useAxios({
    customHandler: err => err && handleAxiosError(err),
    ...args,
    axios: indicoAxios,
  });

  let data = null;
  if (response) {
    data = response.data;
    if (camelize) {
      data = camelizeKeys(data);
    }
    lastData.current = data;
  }
  return {response, error, loading, reFetch, data, lastData: lastData.current};
}

/**
 * React hook to use `setTimeout` inside a react component.
 *
 * @param {Function} callback - the function to run at the end
 * @param {Number} delay - the duration of the timeout (`null` to disable)
 *
 * Based on https://overreacted.io/making-setinterval-declarative-with-react-hooks/
 */
export function useTimeout(callback, delay) {
  const savedCallback = useRef();

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the actual timeout
  useEffect(() => {
    if (delay !== null) {
      const id = setTimeout(() => savedCallback.current(), delay);
      return () => clearTimeout(id);
    }
  }, [delay]);
}
