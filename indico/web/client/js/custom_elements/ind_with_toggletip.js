// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
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
    }

    setup() {
      super.setup();

      // XXX: The tip is an aria-live region. Because of this, it is necessary to clear the content.
      // Live regions are (usually) only announced when content changes. (See also the hide() method.)
      this.tipContent = this.$tip.innerHTML;

      // XXX: Because the toggle tip can contain interactive elements such as links, we must make sure
      // the focusout handler doesn't immediately remove the content before the browser has had a chance
      // to process the click. The delay of 200ms was derived by testing the maximum time between focusin
      // and click events.
      const delayedUnfocusListener = () => {
        clearTimeout(this.timer);
        this.timer = setTimeout(this.hide, 200);
      };

      this.addEventListener('click', evt => {
        // Abort unfocus listener
        clearTimeout(this.timer);

        // XXX: The toggletip button can trigger the toggle tip even when it is still open,
        // so we must clean up just in case.
        this.removeEventListener('focusout', delayedUnfocusListener);
        this.hide();

        const $target = evt.target.closest('button');
        if (!$target || !this.contains($target)) {
          return;
        }
        this.show();
        this.addEventListener('focusout', delayedUnfocusListener, {once: true});
      });
    }
  }
);
