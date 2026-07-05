// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import $ from 'jquery';

beforeEach(() => {
  document.body.innerHTML = '';
  window.$ = $;
  window.jQuery = $;
  global.$ = $;
  global.jQuery = $;
});

describe('dropdown widget accessibility', () => {
  it('adds menu relationships and keeps aria-expanded in sync', () => {
    document.body.innerHTML = `
      <div class="toolbar">
        <button class="i-button" data-toggle="dropdown">Export</button>
        <ul class="i-dropdown"><li><a href="#">CSV</a></li></ul>
      </div>
    `;

    require('jquery-ui/ui/widget');
    require('./dropdown');
    $('.toolbar').dropdown();

    const trigger = $('[data-toggle="dropdown"]');
    const menu = $('.i-dropdown');
    expect(trigger.attr('aria-haspopup')).toBe('menu');
    expect(trigger.attr('aria-expanded')).toBe('false');
    expect(trigger.attr('aria-controls')).toBe(menu.attr('id'));
    expect(menu.attr('role')).toBe('menu');
    expect(menu.find('a').attr('role')).toBe('menuitem');

    trigger.trigger('click');
    expect(trigger.attr('aria-expanded')).toBe('true');

    trigger.trigger('click');
    expect(trigger.attr('aria-expanded')).toBe('false');
  });
});
