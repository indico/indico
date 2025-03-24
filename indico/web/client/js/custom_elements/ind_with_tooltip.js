// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import {TipBase} from 'indico/custom_elements/TipBase';

const tipDelay = 500; // ms

CustomElementBase.defineWhenDomReady(
  'ind-with-tooltip',
  class extends TipBase {
    show() {
      // XXX: Delay showing the tip to prevent tip blinking when moving the cursor over multiple items with tooltips
      clearTimeout(this.timer);
      this.timer = setTimeout(() => {
        this.shown = true;
        this.updatePosition();
      }, tipDelay);
    }

    hide() {
      clearTimeout(this.timer);
      this.shown = false;
    }

    setup() {
      super.setup();

      // XXX: When the tooltip is part of a button/link text, we don't want to trigger the default behavior
      this.$tip.addEventListener('click', evt => {
        evt.preventDefault();
      });

      this.addEventListener('pointerenter', () => {
        this.show();
        this.addEventListener('pointerleave', this.hide, {once: true});
      });

      this.addEventListener('focusin', () => {
        this.removeEventListener('pointerleave', this.hide);
        this.show();
        this.addEventListener('focusout', this.hide);
      });
    }
  }
);
