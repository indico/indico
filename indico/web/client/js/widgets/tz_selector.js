// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// eslint-disable-next-line import/unambiguous
window.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#tz-selector-widget form');
  const tzModes = document.getElementById('tz-modes');
  const customRadio = document.getElementById('tz-mode-custom');
  const tzCustomField = document.querySelector('#tz-custom-field select');

  // No TZ selector?
  if (!form) {
    return;
  }

  tzCustomField.querySelector('option:checked')?.scrollIntoView();

  function setCustomMode() {
    customRadio.checked = true;
  }

  tzCustomField.addEventListener('click', setCustomMode);
  tzCustomField.addEventListener('change', setCustomMode);

  tzModes.addEventListener('change', evt => {
    if (evt.target.value === 'user') {
      tzCustomField.querySelector(`option[value="${evt.target.dataset.userTz}"]`)?.scrollIntoView();
    } else if (evt.target.value === 'custom') {
      tzCustomField.querySelector('option:checked')?.scrollIntoView();
    }
  });

  form.addEventListener('submit', evt => {
    evt.preventDefault();
  });
});
