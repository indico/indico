// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import {focusLost} from 'indico/utils/composite-events';
import {domReady} from 'indico/utils/domstate';
import * as positioning from 'indico/utils/positioning';

import './ind_with_popup.scss';

customElements.define(
  'ind-with-popup',
  class extends CustomElementBase {
    static lastId = 0;

    static observedAttributes = ['shown'];

    get shown() {
      return this.hasAttribute('shown');
    }

    set shown(value) {
      this.toggleAttribute('shown', value);
    }

    constructor() {
      super();
      this.popupId = `ind-with-popup-${this.constructor.lastId++}`;
    }

    setup() {
      domReady.then(() => {
        const trigger = this.querySelector('[data-trigger]');
        const dialog = this.querySelector('[data-dialog]');

        console.assert(trigger && dialog, 'Must have [data-trigger] and [data-dialog] elements');

        dialog.firstElementChild.tabIndex = -1;
        dialog.id = `${this.popupId}-dialog`;
        trigger.setAttribute('aria-haspopup', true);
        trigger.setAttribute('aria-controls', dialog.id);

        trigger.addEventListener('click', () => {
          this.shown = !this.shown;
        });

        this.addEventListener('keydown', evt => {
          if (evt.code === 'Escape') {
            this.shown = false;
            dialog.dispatchEvent(new Event('close'));
          }
        });

        this.addUnmountEventListener(
          focusLost(this, () => {
            this.shown = false;
          })
        );
      });
    }

    attributeChangedCallback() {
      const trigger = this.querySelector('[data-trigger]');
      const dialog = this.querySelector('[data-dialog]');

      trigger.setAttribute('aria-expanded', this.shown);

      if (this.shown) {
        this.toggleAttribute('data-position-check', true);
        positioning.position(dialog, this, positioning.popupPositionStrategy, () => {
          dialog.show();
          dialog.firstElementChild.focus();
          this.removeAttribute('data-position-check');
        });
      } else {
        dialog.close();
      }

      this.dispatchEvent(new Event('toggle', {bubbles: true}));
    }
  }
);
