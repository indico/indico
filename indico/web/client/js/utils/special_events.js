// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export function focusLost(target, callback) {
  const abortFocusLost = new AbortController();
  const listenerOptions = {signal: abortFocusLost.signal};

  const triggerCallbackIfOutsideTarget = evt => {
    if (!target.contains(evt.target)) {
      callback();
    }
  };

  document.body.addEventListener('click', triggerCallbackIfOutsideTarget, listenerOptions);
  document.body.addEventListener('focusin', triggerCallbackIfOutsideTarget, listenerOptions);
  return () => abortFocusLost.abort();
}
