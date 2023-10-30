// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './ind_menu.scss';
import {domReady, getViewportGeometry} from 'indico/utils/domstate';

const HOVER_OUT_TIMEOUT = 500;
let lastId = 0; // Track the assigned IDs to give each element a unique ID

function getListRightCoordinate(container, list) {
  // XXX: Call after the menu is shown
  const {vw} = getViewportGeometry();
  const containerBox = container.getBoundingClientRect();
  const menuBox = list.getBoundingClientRect();
  if (containerBox.left + menuBox.width > vw) {
    return '0';
  }
  return 'auto';
}

customElements.define(
  'ind-menu',
  class extends HTMLElement {
    constructor() {
      super();
      Object.defineProperty(this, 'show', {
        get: () => this.hasAttribute('show'),
        set: value => {
          this.toggleAttribute('show', value);
        },
      });
    }

    connectedCallback() {
      domReady.then(() => {
        let hoverOutTimer;

        this.trigger = this.querySelector('button');
        this.list = this.querySelector('menu');

        // Initial setup
        this.list.id = this.list.id || `dropdown-list-${lastId++}`;
        this.trigger.setAttribute('aria-controls', this.list.id);
        this.updateMenuDisplay();

        this.trigger.addEventListener('click', () => {
          this.show = !this.show;
        });

        this.addEventListener('focusout', () => {
          // Delay action as no element is focused immediately after focusout
          requestAnimationFrame(() => {
            if (this.contains(document.activeElement)) {
              return;
            }
            this.trigger.removeAttribute('aria-expanded');
          });
        });

        this.addEventListener('keydown', evt => {
          if (this.show && evt.code === 'Escape') {
            this.show = false;
            this.trigger.focus();
          }
        });

        this.addEventListener('focusout', () => {
          // XXX: skip frame to see if the next focused element is still inside the menu
          requestAnimationFrame(() => {
            if (!this.contains(document.activeElement)) {
              this.show = false;
            }
          });
        });

        this.addEventListener('pointerleave', () => {
          hoverOutTimer = setTimeout(() => {
            if (!this.contains(document.activeElement)) {
              this.show = false;
            }
          }, HOVER_OUT_TIMEOUT);
        });

        this.addEventListener('pointenter', () => {
          clearTimeout(hoverOutTimer);
        });
      });
    }

    attributeChangedCallback() {
      this.updateMenuDisplay();
    }

    static observedAttributes = ['show'];

    updateMenuDisplay() {
      this.trigger.setAttribute('aria-expanded', this.show);
      if (this.show) {
        requestAnimationFrame(() => {
          this.list.style.setProperty('--right', getListRightCoordinate(this, this.list));
        });
      }
    }
  }
);
