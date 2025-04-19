// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import * as positioning from 'indico/utils/positioning';

import './tips.scss';

CustomElementBase.defineWhenDomReady(
  'ind-with-toggletip',
  class extends CustomElementBase {
    static observedAttributes = ['shown'];

    static attributes = {
      shown: Boolean,
    };

    setup() {
      const trigger = this.querySelector('[data-trigger]');
      const tip = this.querySelector('[data-tip-content]');

      let stopPositioning;
      const tipHTML = tip.innerHTML;

      // Clear the tip initially so that the screen reader will announce it
      // correctly when the tip is opened.
      tip.innerHTML = '';
      tip.tabIndex = -1;

      trigger.addEventListener('click', () => {
        this.shown = !this.shown;
      });

      trigger.addEventListener('blur', () => {
        this.shown = false;
      });

      this.addEventListener('keydown', evt => {
        if (evt.code === 'Escape') {
          this.shown = false;
        }
      });

      this.addEventListener('x-attrchange.shown', () => {
        trigger.setAttribute('aria-expanded', this.shown);
        if (this.shown) {
          tip.innerHTML = tipHTML;
          stopPositioning = positioning.position(
            tip,
            this,
            positioning.verticalTooltipPositionStrategy,
            () => {
              tip.hidden = false;
            }
          );
        } else {
          stopPositioning?.();
          tip.hidden = true;
          tip.innerHTML = '';
        }
      });

      this.onconnect = () => {
        this.addUnmountEventListener(() => {
          stopPositioning?.();
        });
      };
    }
  }
);
