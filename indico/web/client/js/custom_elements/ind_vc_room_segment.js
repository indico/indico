// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './ind_vc_room_segment.scss';
import {domReady} from 'indico/utils/domstate';

let lastId = 0; // Track the assigned IDs to give each element a unique ID

/** Little "segment" bar which show up once per VC room */
customElements.define(
  'ind-vc-room-segment',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        const expand = this.querySelector('.expand-button');
        const list = this.querySelector('.secondary.segment');

        // The segment may include an "expand" button
        if (expand) {
          expand.setAttribute('aria-expanded', false);

          list.id = list.id || `dropdown-list-${lastId++}`;
          expand.setAttribute('aria-controls', list.id);

          expand.addEventListener('click', () => {
            expand.setAttribute('aria-expanded', expand.getAttribute('aria-expanded') !== 'true');
            this.classList.toggle('expanded');
            expand.classList.toggle('active');
            expand.querySelector('i').classList.toggle('down');
            expand.querySelector('i').classList.toggle('up');
            return false;
          });
        }
      });
    }
  }
);
