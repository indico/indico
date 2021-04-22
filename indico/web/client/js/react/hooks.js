// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:core.principals';
import favoriteUsersURL from 'indico-url:users.favorites_api';

import useAxios from '@use-hooks/axios';
import _ from 'lodash';
import PropTypes from 'prop-types';
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {useHistory} from 'react-router-dom';

import {handleAxiosError, indicoAxios} from '../utils/axios';
import {camelizeKeys} from '../utils/case';

export const useFavoriteUsers = (userId = null, lazy = false) => {
  // XXX: this state should ideally be global so if this hook is used more than
  // once on the same page we keep the favorites in sync and don't send multiple
  // requests to load the initial list
  const [favorites, setFavorites] = useState({});
  const [loading, setLoading] = useState(true);
  const [shouldLoad, setShouldLoad] = useState(!lazy);

  const apiCall = useCallback(
    async (method, id = null, source = null) => {
      let response;
      const args = {};
      if (id !== null) {
        args.fav_user_id = id;
      }
      if (userId !== null) {
        args.user_id = userId;
      }
      try {
        response = await indicoAxios.request({
          method,
          url: favoriteUsersURL(args),
          cancelToken: source ? source.token : null,
        });
      } catch (error) {
        handleAxiosError(error);
        return null;
      }
      return response.data;
    },
    [userId]
  );

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

  const load = () => setShouldLoad(true);

  useEffect(() => {
    if (!shouldLoad) {
      return;
    }

    const source = indicoAxios.CancelToken.source();

    (async () => {
      const ids = await apiCall('GET', null, source);
      if (ids === null || !ids.length) {
        setLoading(false);
        return;
      }
      const data = await fetchDetails(ids, source);
      setFavorites(data);
      setLoading(false);
    })();
    return () => {
      source.cancel();
    };
  }, [apiCall, shouldLoad]);

  return [favorites, [add, del, load], loading];
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

export function useIndicoAxios({camelize, unhandledErrors = [], options = {}, ...args}) {
  const lastData = useRef(null);
  if (unhandledErrors.length) {
    options.headers = {
      ...(options.headers || {}),
      'X-Indico-No-Report-Error': unhandledErrors.join(','),
    };
  }
  const {response, error, loading, reFetch} = useAxios({
    customHandler: err =>
      err &&
      (!err.response || !unhandledErrors.includes(err.response.status)) &&
      handleAxiosError(err),
    ...args,
    options,
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
 * A hook that provides an easy way of having a toggle switch whose value is
 * loaded from a url and where toggling it sends PUT/DELETE to the same URL.
 *
 * @param {string} url - a url that accepts GET/PUT/DELETE requests
 * @returns an array consisting of `[value, toggle, loading, saving]`
 */
export function useTogglableValue(url) {
  const [newState, setNewState] = useState(null);
  const [saving, setSaving] = useState(false);
  const {data} = useIndicoAxios({
    url,
    trigger: url,
  });

  useEffect(() => {
    // reset the cached new state in case the url changes.
    // this is VERY unlikely to happen, but let's keep things correct...
    setNewState(null);
  }, [url]);

  // if we don't have initial data yet, we show it as unchecked.
  // it's up to the caller to hide in this case or just disable the toggle
  if (data === null) {
    return [false, () => null, true, false];
  }

  // if we changed the state locally, that one has priority, otherwise use the fetched value
  const checked = newState === null ? data : newState;

  const save = async enabled => {
    try {
      // we are optimistic and flip the switch without waiting for the action to finish
      setSaving(true);
      setNewState(enabled);
      if (enabled) {
        await indicoAxios.put(url);
      } else {
        await indicoAxios.delete(url);
      }
    } catch (error) {
      setSaving(false);
      setNewState(!enabled);
      handleAxiosError(error);
      return;
    }
    setSaving(false);
  };

  return [checked, () => save(!checked), false, saving];
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

/**
 * React hook that parses the query string into an object.
 *
 * Provides an array [query, setQuery] similar to useState and allows adding/updating a parameter or
 * removing it by setting it as undefined.
 *
 * @returns {Array<{object, function}>}
 */
export function useQueryParams() {
  const [query, _setQuery] = useState(window.location.search);
  const queryObject = useMemo(() => Object.fromEntries(new URLSearchParams(query)), [query]);
  const history = useHistory();

  const setQuery = useCallback(
    (type, name, reset) => {
      const params = new URLSearchParams(reset ? undefined : query);
      if (name !== undefined) {
        params.set(type, name);
      } else {
        params.delete(type);
      }
      const _query = params.toString();
      history.push({
        pathname: window.location.pathname,
        search: `?${_query}`,
      });
      _setQuery(_query);
    },
    [history, query]
  );

  useEffect(() => {
    return history.listen(location => _setQuery(location.search));
  }, [history, query, _setQuery]);

  return [queryObject, setQuery];
}
