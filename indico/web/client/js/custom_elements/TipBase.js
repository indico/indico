// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';
import * as positioning from 'indico/utils/positioning';

import './tips.scss';

export class TipBase extends HTMLElement {
  constructor() {
    super();
    this.show = this.show.bind(this);
    this.hide = this.hide.bind(this);
    this.dismiss = this.dismiss.bind(this);
  }

  connectedCallback() {
    domReady.then(() => {
      this.$tip = this.querySelector('[data-tip-content]');
      console.assert(this.$tip, 'Must contain a *[data-tip-content] element');
      this.setup();
    });
  }

  disconnectedCallback() {
    window.removeEventListener('keydown', this.dismiss);
  }

  get orientation() {
    return this.getAttribute('orientation');
  }

  set orientation(value) {
    this.setAttribute('orientation', value);
  }

  get shown() {
    return this.hasAttribute('shown');
  }

  set shown(isShown) {
    if (this.shown === isShown) {
      return;
    }
    this.toggleAttribute('shown', isShown);
    this.dispatchEvent(new Event('toggle'));
  }

  updatePosition() {
    this.style = '';
    const strategy =
      this.orientation === 'horizontal'
        ? positioning.horizontalTooltipPositionStrategy
        : positioning.verticalTooltipPositionStrategy;

    positioning.position(this.$tip, this, strategy);
  }

  dismiss(evt) {
    if (!this.shown || evt.code !== 'Escape') {
      return;
    }
    evt.preventDefault();
    this.shown = false;
  }

  setup() {
    window.addEventListener('keydown', this.dismiss);
    this.$tip.addEventListener('click', evt => {
      evt.preventDefault();
    });
    this.addEventListener('toggle', () => {
      if (this.shown) {
        window.addEventListener('resize', this.updatePosition);
        window.addEventListener('scroll', this.updatePosition, {passive: true});
      } else {
        window.removeEventListener('resize', this.updatePosition);
        window.removeEventListener('scroll', this.updatePosition);
      }
    });
  }
}
