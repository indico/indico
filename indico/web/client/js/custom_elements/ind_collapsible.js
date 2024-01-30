// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';

import './ind_collapsible.scss';

customElements.define(
  'ind-collapsible',
  class extends HTMLElement {
    connectedCallback() {
      domReady.then(() => {
        this.container = this.querySelector('[data-collapsible]');
        this.containerStyle = window.getComputedStyle(this.container);

        console.assert(
          this.container,
          '<ind-collapsible> must have a descendant with a data-collapsible attribute'
        );
        console.assert(
          this.querySelector('button[value="toggle-collapse"]'),
          '<ind-collapsible> must have a descendant button with value="toggle-collapse"'
        );

        this.markCollapsible();

        window.addEventListener('resize', this.markCollapsible);
        window.addEventListener('orientationchange', this.markCollapsible);
        this.addEventListener('click', evt => {
          if (evt.target.closest('button[value="toggle-collapse"]')) {
            this.toggleAttribute('collapsed');
          }
        });
      });
    }

    disconnectedCallback() {
      window.removeEventListener('resize', this.markCollapsible);
      window.removeEventListener('orientationchange', this.markCollapsible);
    }

    markCollapsible = () => {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        const children = this.container.children;
        let lastChildAboveCutOff = children[0];
        let linesFound = 1;
        const cutOffLines = Number(this.getAttribute('lines'));

        // Skip the first child, since it's guaranteed to be on the first line.
        for (let i = 1, child; (child = children[i++]); ) {
          if (lastChildAboveCutOff.offsetTop === child.offsetTop) {
            continue;
          }
          linesFound++;
          if (linesFound > cutOffLines) {
            // We have crossed the cutOffLines threshold, so no need to test further
            break;
          }
          lastChildAboveCutOff = child;
        }

        const collapsible = linesFound > cutOffLines;
        this.toggleAttribute('collapsible', collapsible);

        if (collapsible) {
          const contentHeight =
            lastChildAboveCutOff.offsetTop +
            lastChildAboveCutOff.offsetHeight -
            children[0].offsetTop;
          const containerPadding = this.containerStyle.getPropertyValue('padding-top');

          this.style.setProperty(
            '--collapsed-height',
            `calc(${contentHeight}px + ${containerPadding})`
          );
        } else {
          this.style.setProperty('--collapsed-height', 'auto');
        }
      }, 100);
    };
  }
);
