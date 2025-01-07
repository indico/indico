// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * Controller that will toggle something on and automatically back off after a delay
 */
export class DelayedAutoToggleController {
  constructor(onAction, offAction, delay = 0) {
    this.onAction = onAction;
    this.offAction = offAction;
    this.delay = delay;
    this.timer = null;
  }

  activate() {
    this.onAction();
    this.timer = setTimeout(() => this.offAction(), this.delay);
  }

  reset() {
    clearTimeout(this.timer);
    this.offAction();
  }
}
