// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as positioning from 'indico/utils/positioning';

export function onFocusout(element, callback) {
  let clickedInside = false;

  element.addEventListener(
    'pointerdown',
    () => {
      clickedInside = true;
      setTimeout(() => {
        clickedInside = false;
      });
    },
    {capture: true}
  );

  element.addEventListener(
    'focusout',
    () => {
      if (clickedInside) {
        clickedInside = false;
        return;
      }
      setTimeout(() => {
        if (!element.contains(document.activeElement)) {
          callback();
        }
      });
    },
    {capture: true}
  );
}

export function onKeyboardNavigation(element, options) {
  const defaultHandler = nextItem => {
    nextItem.focus();
  };
  const {
    activeItemSelector = 'li:focus-within',
    next = defaultHandler, // Pass null to suppress default behavior
    prev = defaultHandler,
    first = defaultHandler,
    last = defaultHandler,
  } = options;

  element.addEventListener('keyup', evt => {
    switch (evt.key) {
      case 'ArrowDown': {
        evt.preventDefault();
        const activeItem = element.querySelector(activeItemSelector);
        const nextItem = activeItem?.nextElementSibling || element.firstElementChild;
        next?.(nextItem, activeItem, evt);
        break;
      }
      case 'ArrowUp': {
        evt.preventDefault();
        const activeItem = element.querySelector(activeItemSelector);
        const nextItem = activeItem?.previousElementSibling || element.lastElementChild;
        prev?.(nextItem, activeItem, evt);
        break;
      }
      case 'Home': {
        evt.preventDefault();
        const activeItem = element.querySelector(activeItemSelector);
        const nextItem = element.firstElementChild;
        first?.(nextItem, activeItem, evt);
        break;
      }
      case 'End': {
        evt.preventDefault();
        const activeItem = element.querySelector(activeItemSelector);
        const nextItem = element.lastElementChild;
        last?.(nextItem, activeItem, evt);
        break;
      }
    }
  });
}

export class Observer {
  constructor() {
    this.cleanupControllers = new Map();
  }

  observe(target, eventMap) {
    this.cleanupControllers.get(target)?.abort();
    this.cleanupControllers.delete(target);

    const cleanupController = new AbortController();
    this.cleanupControllers.set(target, cleanupController);

    target.addEventListener(
      'cleanup',
      () => {
        cleanupController.abort();
      },
      {signal: cleanupController.signal}
    );

    for (const eventName in eventMap) {
      const handler = this[eventMap[eventName]].bind(this);
      target.addEventListener(eventName, handler, {signal: cleanupController.signal});
    }
  }

  cleanup() {
    for (const controller of this.cleanupControllers.values()) {
      controller.abort();
    }
    this.cleanupControllers.clear();
  }
}

export class Observable extends EventTarget {
  notify(eventName, detail = {}) {
    this.dispatchEvent(new CustomEvent(eventName, {detail}));
  }

  cleanup() {
    this.notify('cleanup');
  }
}

export class DropdownPositioning extends Observer {
  constructor(anchor, positioned) {
    super();
    this.abortPositioning = null;
    this.anchor = anchor;
    this.positioned = positioned;
  }

  start() {
    this.abortPositioning = positioning.position(
      this.positioned,
      this.anchor,
      positioning.dropdownPositionStrategy,
      () => {}
    );
  }

  stop() {
    this.abortPositioning?.();
  }
}

export class Expandable extends Observable {
  constructor(id, trigger, popup) {
    super();
    this.id = id;
    this.trigger = trigger;
    this.popup = popup;
  }

  expand() {
    this.trigger.setAttribute('aria-expanded', true);
    this.popup.hidden = false;
    this.notify('expand');
  }

  collapse() {
    this.trigger.setAttribute('aria-expanded', false);
    this.popup.hidden = true;
    this.notify('collapse');
  }

  collapseAndRefocus() {
    this.collapse();
    this.trigger.focus();
  }

  get isCollapsed() {
    return this.trigger.getAttribute('aria-expanded') === 'false';
  }

  toggle() {
    if (this.isCollapsed) {
      this.expand();
    } else {
      this.collapse();
    }
  }

  init() {
    this.collapse();
    this.popup.id ||= this.id;
    this.trigger.setAttribute('aria-controls', this.popup.id);
  }
}

export class PopupWithTrigger {
  constructor(expandable) {
    this.expandable = expandable;
    this.closedViaFocusout = false;
    this.clickedInside = false;
  }

  setup(closeDelay = 200) {
    // Track clicks inside the popup to prevent closing on label/checkbox clicks
    this.expandable.popup.addEventListener(
      'pointerdown',
      () => {
        this.clickedInside = true;
        setTimeout(() => {
          this.clickedInside = false;
        });
      },
      {capture: true}
    );

    this.expandable.trigger.addEventListener('click', () => {
      if (this.closedViaFocusout) {
        return;
      }
      this.expandable.toggle();
    });

    this.expandable.popup.addEventListener('focusout', evt => {
      // If clicked inside the popup, don't close
      if (this.clickedInside) {
        this.clickedInside = false;
        return;
      }

      // If focus is moving within the popup, don't close
      if (evt.relatedTarget && this.expandable.popup.contains(evt.relatedTarget)) {
        return;
      }

      // Wait for focus to settle before checking if it actually left
      setTimeout(() => {
        if (this.expandable.popup.contains(document.activeElement)) {
          return;
        }
        this.expandable.collapse();
        this.closedViaFocusout = true;
        setTimeout(() => {
          this.closedViaFocusout = false;
        }, closeDelay);
      });
    });
  }
}
