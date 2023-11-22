// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';

customElements.define(
  'ind-toggle-trigger',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        this.triggerElement = this.querySelector('[aria-controls]');

        console.assert(this.triggerElement, '<ind-toggle-trigger> must include a button or a link');

        this.controlledElement = document.getElementById(
          this.triggerElement.getAttribute('aria-controls')
        );

        if (!this.controlledElement) {
          this.triggerElement.hidden = true;
        } else {
          this.syncState();
          this.controlledElement.addEventListener('toggle', this.syncState);
          this.triggerElement.addEventListener('click', this.toggleControlledElement);
        }
      });
    }

    disconnectedCallback() {
      this.controlledElement.removeEventListener('toggle', this.syncState);
    }

    syncState = () => {
      this.triggerElement.setAttribute('aria-expanded', !this.controlledElement.hidden);
    };

    toggleControlledElement = () => {
      this.controlledElement.hidden = !this.controlledElement.hidden;
      this.controlledElement.dispatchEvent(new Event('toggle', {bubbles: true}));
    };
  }
);
