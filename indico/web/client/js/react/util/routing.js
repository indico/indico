// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useRouteMatch, useParams} from 'react-router-dom';

/**
 * Creates a path suitable for usage in react-router.
 *
 * All dynamic params are using the standard `:param` match of react-router,
 * so there are no special checks for types/values when using e.g. the `int`
 * or `any` converters in Python.
 *
 * @param {Function} urlFunc - the flask URL builder function to use
 * @param {string[]} dynamicParams - any params that should use dynamic matches
 * @param {Object.<string,string>} params - any params that should be interpolated in the
 * url; those will not be exposed in the params of the matching Route
 */
export function routerPathFromFlask(urlFunc, dynamicParams, params = {}) {
  const urlArgs = {...params};
  dynamicParams.forEach(p => {
    // `:foo` would be url-encoded so we use `__foo__` and replace it after building the url
    urlArgs[p] = `__${p}__`;
  });
  return dynamicParams.reduce((url, p) => url.replace(`__${p}__`, `:${p}`), urlFunc(urlArgs));
}

/**
 * This hook provides the dynamic params from a Flask URL rule client-side.
 * It relies on react-router so it only works for componends inside a Router.
 *
 * All params are using the standard `:param` match of react-router, so there
 * are no special checks for types/values when using e.g. the `int` or `any`
 * converters in Python.
 *
 * @param {Function} urlFunc - the flask URL builder function to use
 * @param {string[]} params - the list of params the flask rule requires
 */
export function useFlaskRouteParams(urlFunc, params) {
  const match = useRouteMatch(routerPathFromFlask(urlFunc, params));
  return match ? match.params : null;
}

/**
 * This hook retrieves a single param from the router and converts it to a number.
 *
 * @param {string} name - the name of the router param to retrieve
 */
export function useNumericParam(name) {
  const params = useParams();
  const value = params[name];
  if (value === undefined) {
    return null;
  }
  return parseInt(value, 10);
}
