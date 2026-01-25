// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {onKeyboardNavigation, DropdownPositioning, Expandable, PopupWithTrigger} from './shared';

export default class Menu {
  static lastId = 0;

  constructor(root, trigger = root.querySelector('button'), list = root.querySelector('menu, ul')) {
    this.root = root;
    this.trigger = trigger ?? root.querySelector('button');
    this.list = list ?? root.querySelector('menu, ul');

    this.menu = new Expandable(`menu-${this.constructor.lastId++}`, trigger, list);
    this.positioning = new DropdownPositioning(root, list);
    this.positioning.observe(this.menu, {expand: 'start', collapse: 'stop'});
    this.focusableElementSelector = 'button,a,input,select,textarea';
  }

  setup() {
    this.menu.init();

    const popupWithTrigger = new PopupWithTrigger(this.menu);
    popupWithTrigger.setup();

    this.menu.addEventListener('expand', () => {
      setTimeout(() => this.list.querySelector(this.focusableElementSelector).focus(), 100);
    });

    this.trigger.addEventListener('keydown', evt => {
      if (evt.code === 'Escape' && !this.menu.isCollapsed) {
        evt.preventDefault();
        this.menu.collapseAndRefocus();
      }
    });

    this.trigger.addEventListener('keydown', evt => {
      if (evt.code === 'ArrowDown' && this.menu.isCollapsed) {
        this.menu.expand();
      }
    });

    onKeyboardNavigation(this.list, {
      activeItemSelector: 'li:focus-within',
      next: nextItem => {
        nextItem.querySelector(this.focusableElementSelector).focus();
      },
      prev: nextItem => {
        nextItem.querySelector(this.focusableElementSelector).focus();
      },
    });

    delete this.setup;
  }

  static setup(root) {
    const menu = new this(root);
    menu.setup();
    return menu;
  }
}
