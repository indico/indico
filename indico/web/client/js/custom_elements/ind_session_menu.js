// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate.js';

customElements.define(
  'ind-session-menu',
  class extends HTMLElement {
    static observedAttributes = ['hidden'];

    connectedCallback() {
      domReady.then(() => {
        this.ready = true;
      });
    }

    attributeChangedCallback(name, value, prevValue) {
      if (name !== 'hidden' || !this.ready) {
        return;
      }

      this.toggleAnimate(prevValue);
    }

    toggleAnimate(prevValue) {
      if (matchMedia?.('(prefers-reduced-motion)').matches) {
        return;
      }

      if (prevValue === null) {
        // hidden -> shown
        const height = `${this.offsetHeight}px`;
        this.animate([{height: 0, overflow: 'hidden'}, {height, overflow: 'hidden'}], {
          duration: 200,
        });
      } else {
        // shown -> hidden
        this.style.display = 'flex';
        requestAnimationFrame(() => {
          const height = `${this.offsetHeight}px`;
          this.style.display = '';
          this.animate(
            [{height, display: 'flex', overflow: 'hidden'}, {height: 0, overflow: 'hidden'}],
            {
              duration: 200,
            }
          );
        });
      }
    }
  }
);
