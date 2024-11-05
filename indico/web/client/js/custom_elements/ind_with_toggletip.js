// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {TipBase} from 'indico/custom_elements/TipBase';

const liveRegionUpdateDelay = 100;

customElements.define(
  'ind-with-toggletip',
  class extends TipBase {
    show() {
      // XXX: We add a slight delay to ensure that the screen readers will be able to pick up
      // the change to the live region.
      setTimeout(() => {
        this.$tip.innerHTML = this.tipContent;
        this.shown = true;
        this.updatePosition();
      }, liveRegionUpdateDelay);
    }

    hide() {
      this.shown = false;
      this.$tip.hidden = true;
      this.$tip.innerHTML = '';
    }

    setup() {
      super.setup();

      this.addEventListener('click', evt => {
        const $target = evt.target.closest('button');
        if (!$target || !this.contains($target)) {
          return;
        }

        if (this.shown) {
          $target.removeAttribute('aria-expanded');
          this.removeEventListener('focusout', this.hide);
          this.hide();
        } else {
          $target.setAttribute('aria-expanded', true);
          this.show();
          this.addEventListener('focusout', this.hide, {once: true});
        }
      });
    }
  }
);
