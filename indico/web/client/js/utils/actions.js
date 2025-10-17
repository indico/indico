// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from './domstate';

function handleAction(evt) {
  const actionElement = evt.target.closest('[data-action]:is(a, button)');
  const action = actionElement?.dataset.action;

  if (!action) {
    return;
  }

  // Prevent default unless explicitly allowed
  if (!actionElement.dataset.actionAllowDefault) {
    evt.preventDefault();
  }

  // Dispatch action

  const eventName = `indico:action:${action}`;
  const detail = {
    trigger: actionElement,
    originalEvent: evt,
    // Include all data-* attributes as camelCase properties
    ...Object.fromEntries(
      Object.entries(actionElement.dataset).map(([key, value]) => [key, value])
    ),
  };

  const customEvent = new CustomEvent(eventName, {
    bubbles: true,
    cancelable: true,
    detail,
  });

  actionElement.dispatchEvent(customEvent);
}

domReady.then(() => {
  document.addEventListener('click', handleAction);
});
