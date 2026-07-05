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
  jest.resetModules();
});

describe('handleRowSelection', () => {
  it('removes disabled selected-row actions from the tab order and restores them after selection', () => {
    document.body.innerHTML = `
      <div class="list">
        <table class="i-table"><tbody><tr><td><input class="select-row" type="checkbox"></td></tr></tbody></table>
        <button class="js-requires-selected-row disabled">Remove</button>
        <a href="#" class="js-requires-selected-row disabled" tabindex="2">Export</a>
      </div>
    `;

    require('./list_generator');
    window.handleRowSelection(true);

    expect($('.js-requires-selected-row').eq(0).attr('aria-disabled')).toBe('true');
    expect($('.js-requires-selected-row').eq(0).attr('tabindex')).toBe('-1');
    expect($('.js-requires-selected-row').eq(1).attr('aria-disabled')).toBe('true');
    expect($('.js-requires-selected-row').eq(1).attr('tabindex')).toBe('-1');

    $('.select-row').prop('checked', true).trigger('change');

    expect($('.js-requires-selected-row').eq(0).attr('aria-disabled')).toBe('false');
    expect($('.js-requires-selected-row').eq(0).attr('tabindex')).toBeUndefined();
    expect($('.js-requires-selected-row').eq(1).attr('aria-disabled')).toBe('false');
    expect($('.js-requires-selected-row').eq(1).attr('tabindex')).toBe('2');
  });
});
