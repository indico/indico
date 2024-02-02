// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';

customElements.define(
  'ind-tz-form',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        const form = this.querySelector('form');
        const customModeRadio = form.querySelector('[value="custom"]');
        const customTzSelect = form.querySelector('[name=tz]');

        function setCustomMode() {
          customModeRadio.checked = true;
        }

        customTzSelect.addEventListener('click', setCustomMode);
        customTzSelect.addEventListener('change', setCustomMode);
      });
    }
  }
);
