// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import * as positioning from 'indico/utils/positioning';

import './tips.scss';

export class TipBase extends CustomElementBase {
  constructor() {
    super();
    this.show = this.show.bind(this);
    this.hide = this.hide.bind(this);
    this.dismiss = this.dismiss.bind(this);
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

    this.toggleAttribute('data-position-check', true);
    const stopPositioning = positioning.position(this.$tip, this, strategy, () => {
      this.removeAttribute('data-position-check');
    });
    this.addEventListener('toggle', stopPositioning, {once: true});
  }

  dismiss(evt) {
    if (!this.shown || evt.code !== 'Escape') {
      return;
    }
    evt.preventDefault();
    this.shown = false;
  }

  setup() {
    this.$tip = this.querySelector('[data-tip-content]');

    console.assert(this.$tip, 'Must contain a *[data-tip-content] element');

    this.addEventListener('x-connect', () => {
      window.addEventListener('keydown', this.dismiss);
    });
    this.addEventListener('x-disconnect', () => {
      window.removeEventListener('keydown', this.dismiss);
    });
    this.addEventListener('x-connect', () => {
      this.contentMutationObserver = new MutationObserver(() => {
        this.updatePosition();
      }).observe(this.$tip, {
        subtree: true,
        childList: true,
        characterData: true,
      });
    });
    this.addEventListener('x-disconnect', () => {
      this.contentMutationObserver.disconnect();
    });
    this.$tip.addEventListener('click', evt => {
      evt.preventDefault();
    });
  }
}
