// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';
import './tips.scss';

let viewportWidth = document.documentElement.clientWidth;
let viewportHeight = document.documentElement.clientHeight;

domReady.then(() => requestIdleCallback(updateClientGeometry));
window.addEventListener('resize', updateClientGeometry);
window.addEventListener('orientationchange', updateClientGeometry);

function updateClientGeometry() {
  viewportWidth = document.documentElement.clientWidth;
  viewportHeight = document.documentElement.clientHeight;
}

function positionVertically(referenceRect, tooltipRect) {
  const vw = viewportWidth;
  const vh = viewportHeight;
  let top = 'auto';
  let bottom = 'auto';
  const refCenter = `${referenceRect.left + referenceRect.width / 2}px`;
  let arrowBorder;

  // Place above or below?
  if (tooltipRect.height < referenceRect.top) {
    bottom = `${vh - referenceRect.top}px`;
    arrowBorder = 'var(--tooltip-surface-color) transparent transparent';
  } else {
    top = `${referenceRect.bottom}px`;
    arrowBorder = 'transparent transparent var(--tooltip-surface-color)';
  }

  // Ideal left coordinate (CSS will adjust as needed)
  const idealLeft = referenceRect.left + (referenceRect.width - tooltipRect.width) / 2;
  // NB: the clamp() formula assumes the tooltip content will always fit the viewport, which is ensured using CSS
  const left = `clamp(0.5em, ${idealLeft}px, ${vw - tooltipRect.width}px - 0.5em)`;

  return {
    top,
    bottom,
    left,
    'right': 'auto',
    'ref-center': refCenter,
    'arrow-borders': arrowBorder,
  };
}

function positionHorizontally(referenceRect, tooltipRect) {
  const vw = viewportWidth;
  const vh = viewportHeight;
  let left = 'auto';
  let right = 'auto';
  const refCenter = `${referenceRect.top + referenceRect.height / 2}px`;
  let arrowBorder;

  // Place right or left?
  if (tooltipRect.width < vw - (referenceRect.x + referenceRect.width)) {
    left = `${referenceRect.x + referenceRect.width}px`;
    arrowBorder = 'transparent var(--tooltip-surface-color) transparent transparent';
  } else {
    right = `${vw - referenceRect.x}px`;
    arrowBorder = 'transparent transparent var(--tooltip-surface-color) transparent';
  }

  // Ideal top coordinate (CSS will adjust as needed)
  const idealTop = referenceRect.top + (referenceRect.height - tooltipRect.height) / 2;
  // NB: the clamp() formula assumes the tooltip content will always fit the viewport, which is ensured using CSS
  const top = `clamp(0.5em, ${idealTop}px, ${vh - tooltipRect.height}px - 0.5em)`;

  return {
    top,
    'bottom': 'auto',
    left,
    right,
    'ref-center': refCenter,
    'arrow-borders': arrowBorder,
  };
}

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

  getTipCSS() {
    const referenceRect = this.getBoundingClientRect();
    const tooltipRect = this.$tip.getBoundingClientRect();

    if (this.orientation === 'horizontal') {
      return positionHorizontally(referenceRect, tooltipRect);
    } else {
      return positionVertically(referenceRect, tooltipRect);
    }
  }

  updatePosition() {
    this.style = '';
    const css = this.getTipCSS();
    for (const key in css) {
      this.style.setProperty(`--${key}`, css[key]);
    }
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
