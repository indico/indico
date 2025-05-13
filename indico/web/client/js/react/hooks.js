// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:core.principals';
import favoriteUsersURL from 'indico-url:users.favorites_api';

import {makeUseAxios} from 'axios-hooks';
import _ from 'lodash';
import PropTypes from 'prop-types';
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {useHistory} from 'react-router-dom';

import {handleAxiosError, indicoAxios} from '../utils/axios';
import {camelizeKeys} from '../utils/case';

const useAxios = makeUseAxios({
  axios: indicoAxios,
  defaultOptions: {
    ssr: false,
    useCache: false,
  },
});

export const useFavoriteUsers = (userId = null, lazy = false) => {
  // XXX: this state should ideally be global so if this hook is used more than
  // once on the same page we keep the favorites in sync and don't send multiple
  // requests to load the initial list
  const [favorites, setFavorites] = useState({});
  const [loading, setLoading] = useState(true);
  const [shouldLoad, setShouldLoad] = useState(!lazy);

  const apiCall = useCallback(
    async (method, id = null, signal = null) => {
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
          signal,
        });
      } catch (error) {
        handleAxiosError(error);
        return null;
      }
      return response.data;
    },
    [userId]
  );

  const fetchDetails = async (ids, signal = null) => {
    const values = ids.map(id => `User:${id}`);
    let response;
    try {
      response = await indicoAxios.post(principalsURL(), {values}, {signal});
    } catch (error) {
      handleAxiosError(error);
      return null;
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

    const controller = new AbortController();

    (async () => {
      const ids = await apiCall('GET', null, controller.signal);
      if (ids === null || !ids.length) {
        setLoading(false);
        return;
      }
      const data = await fetchDetails(ids, controller.signal);
      if (data !== null) {
        setFavorites(data);
      }
      setLoading(false);
    })();
    return () => {
      controller.abort();
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

/**
 * A hook that provides a declarative way to make an HTTP request with Axios.
 *
 * @param {object|String} axiosConfig - the url or an axios config object
 * @param {object} hookConfig - settings for this hook and useAxios
 *
 * See https://github.com/simoneb/axios-hooks for details on what can be used in the hookConfig.
 * The most interesting one is `{manual: true}` if the request should not be sent automatically
 * but only when `reFetch` is called explicitly; `{useCache: true}` may be useful in some cases
 * as well.
 */
export function useIndicoAxios(
  axiosConfig,
  {camelize = false, skipCamelize = null, unhandledErrors = [], ...hookConfig} = {}
) {
  const lastData = useRef(null);
  const lastError = useRef(null);
  if (typeof axiosConfig === 'string') {
    axiosConfig = {url: axiosConfig};
  }
  if (unhandledErrors.length) {
    axiosConfig.headers = {
      ...(axiosConfig.headers || {}),
      'X-Indico-No-Report-Error': unhandledErrors.join(','),
    };
  }
  const [{loading, error, response}, reFetch, cancel] = useAxios(axiosConfig, hookConfig);

  let data = null;
  if (response) {
    data = response.data;
    if (camelize) {
      data = camelizeKeys(data, skipCamelize);
    }
    lastData.current = data;
  } else if (
    error &&
    lastError.current !== error &&
    (!error.response || !unhandledErrors.includes(error.response.status))
  ) {
    // only run error handler once even if the component using this hook re-renders
    lastError.current = error;
    _.defer(() => handleAxiosError(error));
  }
  return {response, error, loading, reFetch, data, lastData: lastData.current, cancel};
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
  const {data} = useIndicoAxios(url);

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
 * React hook to use `setInterval` inside a react component.
 *
 * @param {Function} callback - the function to run at the end
 * @param {Number} delay - the duration of the timeout (`null` to disable)
 *
 * Based on https://overreacted.io/making-setinterval-declarative-with-react-hooks/
 */
export function useInterval(callback, delay) {
  const savedCallback = useRef();

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the actual interval
  useEffect(() => {
    if (delay !== null) {
      const id = setInterval(() => savedCallback.current(), delay);
      return () => clearInterval(id);
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
    (key, value, reset) => {
      const params = new URLSearchParams(reset ? undefined : query);
      if (value !== undefined) {
        if (Array.isArray(value)) {
          params.delete(key);
          value.forEach(v => params.append(key, v));
        } else {
          params.set(key, value);
        }
      } else {
        params.delete(key);
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

/**
 * React hook to debounce a final-form async validation function.
 */
export function useDebouncedAsyncValidate(validate, milliseconds = 250) {
  const timeout = useRef(null);
  const lastValue = useRef(null);
  const lastResult = useRef(null);

  return (value, values, meta) =>
    new Promise(resolve => {
      if (timeout.current) {
        timeout.current();
      }

      if (value === lastValue.current) {
        resolve(lastResult.current);
        return;
      }

      const timerId = setTimeout(() => {
        lastValue.current = value;
        lastResult.current = validate(value, values, meta);
        resolve(lastResult.current);
      }, milliseconds);

      timeout.current = () => {
        clearTimeout(timerId);
        resolve();
      };
    });
}

/**
 * When combining native JavaScript components with React, React may
 * suppress some events when the input values are manipulated by the
 * event handlers after the native event is dispatched. In such cases,
 * we use the native event handler instead of React's onChange.
 *
 * In most cases this should work fine as long as the callback does not
 * specifically expect the React's SyntheticEvent instance.
 */
export function useNativeEvent(ref, eventType, callback, options = {}) {
  useEffect(() => {
    const node = ref.current;
    node.addEventListener(eventType, callback, options);
    return () => node.removeEventListener(eventType, callback);
  }, [ref, eventType, callback, options]);
}

// Keys not intended for the key sink in the
// useVerticalArrowNavigation() hook.
const NOT_FOR_KEY_SINK = new Set([
  'Space',
  'Tab',
  'Enter',
  'ShiftLeft',
  'ShiftRight',
  'AltLeft',
  'AltRight',
  'ControlLeft',
  'ControlRight',
]);

/**
 * Instrument the container to allow vertical navigation
 * using arrow keys.
 *
 * This hook deals with two kinds of elements within the
 * subtree:
 *
 * - stops - elements where focus should go when the
 *   up/down arrows are pressed
 * - key sink - an element that will receive *all other*
 *   key events, except Tab, Space and Enter
 *
 * The key sink is usually a text input. If absent, the
 * key events are treated as usual.
 *
 * To mark an element as a stop, simply give it a
 * `data-stop` attribute with no value or any value.
 */
export function useVerticalArrowNavigation(containerRef, keySinkRef) {
  useEffect(() => {
    const abortCtrl = new AbortController();

    containerRef.current.addEventListener(
      'keydown',
      evt => {
        if (evt.code === 'ArrowUp' || evt.code === 'ArrowDown') {
          evt.preventDefault();

          const stops = [...evt.currentTarget.querySelectorAll('[data-stop]')];
          const currentStopIndex = stops.indexOf(document.activeElement);
          const isDownward = evt.code === 'ArrowDown';
          let nextStop;

          if (isDownward) {
            nextStop = stops[currentStopIndex + 1] ?? stops[0];
          } else {
            nextStop = stops[currentStopIndex - 1] ?? stops.at(-1);
          }

          nextStop.focus();
        } else if (!NOT_FOR_KEY_SINK.has(evt.code)) {
          keySinkRef?.current?.focus();
        }
      },
      {signal: abortCtrl.signal}
    );

    return () => abortCtrl.abort();
  }, [containerRef, keySinkRef]);
}
