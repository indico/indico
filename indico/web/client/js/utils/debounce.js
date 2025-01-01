// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * This util creates an async debouncer that will only call the function
 * passed to it after not having been called again for the indicated delay.
 *
 * @param {Number} delay - the time after which to trigger
 */
export function makeAsyncDebounce(delay) {
  let timer = null;
  let promise = null;
  let resolve = null;
  let reject = null;
  return fn => {
    if (promise === null) {
      // if we aren't running yet, create a new promise to return to our caller
      promise = new Promise((res, rej) => {
        resolve = res;
        reject = rej;
      });
    }
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
    timer = setTimeout(async () => {
      try {
        const result = await fn();
        resolve(result);
      } catch (e) {
        reject(e);
      }
      // reset state for a fresh debounce cycle
      promise = null;
      timer = null;
    }, delay);
    return promise;
  };
}
