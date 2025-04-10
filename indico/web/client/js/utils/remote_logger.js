// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/*
This module is for DEVELOPMENT ONLY.
Do not leave it imported in production code.

This module is intended as a workaround for cases where the
developer tools are not available on the client-side (e.g.,
when using BrowserStack). Remove the import after usage.

For this to work, you need to run:

  python bin/util/logger.py

Once it's up and running, you will be able to import this module
and call console.log() normally to see its output in the server's
terminal.
*/

// eslint-disable-next-line import/unambiguous
const LOGGER_URL = `http://${location.hostname}:9999/`;
const originalLog = console.log;

const send =
  typeof navigator?.sendBeacon === 'function'
    ? payload => navigator.sendBeacon(LOGGER_URL, new Blob([payload], {type: 'text/plain'}))
    : payload => fetch(LOGGER_URL, {method: 'POST', body: payload});

console.log = (...args) => {
  originalLog(...args);

  const formatted = args
    .map(arg => {
      if (typeof arg === 'object' && arg !== null) {
        try {
          return JSON.stringify(arg, null, 2);
        } catch {
          if (typeof arg.cloneNode === 'function') {
            const copy = arg.cloneNode(true);
            copy.replaceChildren();
            return copy.outerHTML;
          }

          const name = arg.constructor?.name || 'Object';
          let preview;

          try {
            preview = String(arg);
          } catch {
            preview = '[unstringifiable]';
          }
          return `${name}<'${preview}'>`;
        }
      }
      return String(arg);
    })
    .join(' ');
  send(formatted);
};
