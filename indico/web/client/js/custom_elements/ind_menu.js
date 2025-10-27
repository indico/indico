// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './ind_menu.scss';
import CustomElementBase from 'indico/custom_elements/_base';
import * as positioning from 'indico/utils/positioning';

let lastId = 0; // Track the assigned IDs to give each element a unique ID

CustomElementBase.defineWhenDomReady(
  'ind-menu',
  class extends CustomElementBase {
    setup() {
      const indMenu = this;
      const trigger = this.querySelector('button');
      const list = this.querySelector('menu');

      console.assert(
        trigger.nextElementSibling === list,
        'The <menu> element must come after <button>'
      );

      trigger.setAttribute('aria-expanded', false);

      list.id = list.id || `dropdown-list-${lastId++}`;
      trigger.setAttribute('aria-controls', list.id);

      let abortPositioning;

      trigger.addEventListener('click', () => {
        const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
        if (isExpanded) {
          abortPositioning?.();
          trigger.setAttribute('aria-expanded', false);
          list.hidden = true;
          indMenu.removeAttribute('open');
        } else {
          trigger.setAttribute('aria-expanded', true);
          list.hidden = false;
          abortPositioning = positioning.position(
            list,
            trigger,
            positioning.dropdownPositionStrategy,
            () => indMenu.toggleAttribute('open', true)
          );
        }
      });

      this.addEventListener('focusout', () => {
        // Delay action as no element is focused immediately after focusout
        requestAnimationFrame(() => {
          if (this.contains(document.activeElement)) {
            return;
          }
          abortPositioning?.();
          trigger.removeAttribute('aria-expanded');
          list.hidden = true;
          indMenu.removeAttribute('open');
        });
      });

      this.addEventListener('keydown', evt => {
        if (!trigger.hasAttribute('aria-expanded')) {
          return;
        }
        if (evt.code === 'Escape') {
          abortPositioning?.();
          trigger.removeAttribute('aria-expanded');
          list.hidden = true;
          indMenu.removeAttribute('open');
          trigger.focus();
        }
      });
    }
  }
);
