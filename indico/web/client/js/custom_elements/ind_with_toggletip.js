// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import {domReady} from 'indico/utils/domstate';
import * as positioning from 'indico/utils/positioning';
import {focusLost} from 'indico/utils/special_events';

import './tips.scss';

customElements.define(
  'ind-with-toggletip',
  class extends CustomElementBase {
    constructor() {
      super();

      Object.defineProperty(this, 'shown', {
        get() {
          return this.hasAttribute('shown');
        },
        set(val) {
          this.toggleAttribute('shown', val);
        },
      });
    }

    static observedAttributes = ['shown'];

    attributeChangedCallback() {
      const tip = this.querySelector('[data-tip-content]');

      this.stopHandlingFocusLost?.();
      this.stopPositioning?.();

      if (this.shown) {
        this.toggleAttribute('data-position-check', true);
        tip.innerHTML = this._tipHTML;
        tip.hidden = false;
        this.stopPositioning = positioning.position(
          tip,
          this,
          positioning.verticalTooltipPositionStrategy,
          () => {
            this.removeAttribute('data-position-check');
          }
        );
        this.stopHandlingFocusLost = focusLost(this, () => {
          this.shown = false;
        });
      } else {
        tip.innerHTML = '';
        tip.hidden = true;
      }
    }

    setup() {
      domReady.then(() => {
        const trigger = this.querySelector('button');
        const tip = this.querySelector('[data-tip-content]');
        this._tipHTML = tip.innerHTML;

        // Clear the tip initially so that the screen reader will announce it
        // correctly when the tip is opened.
        tip.innerHTML = '';

        trigger.addEventListener('click', () => {
          this.shown = !this.shown;
        });

        this.addEventListener('keydown', evt => {
          if (evt.code === 'Escape') {
            this.shown = false;
          }
        });
      });

      this.onconnect = () => {
        this.addUnmountEventListener(() => {
          this.stopHandlingFocusLost?.();
          this.stopPositioning?.();
        });
      };
    }
  }
);
