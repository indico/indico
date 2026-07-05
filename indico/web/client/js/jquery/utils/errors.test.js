// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import $ from 'jquery';

jest.mock('indico/react/errors', () => jest.fn());
jest.mock('indico/utils/i18n', () => ({
  $T: {
    gettext: text => text,
  },
}));

beforeEach(() => {
  document.body.innerHTML = '';
  window.$ = $;
  window.jQuery = $;
  global.$ = $;
  global.jQuery = $;
  $.fn.stickyTooltip = jest.fn();
});

describe('showFormErrors', () => {
  it('links server-side error messages to the invalid field', () => {
    document.body.innerHTML = `
      <form class="i-form">
        <div class="form-group has-error">
          <div class="form-field" data-error="<ul><li>Enter a title</li></ul>">
            <input id="title" aria-describedby="title-help">
          </div>
        </div>
      </form>
    `;

    expect($('body').find('.i-form .has-error > .form-field')).toHaveLength(1);

    require('./errors');
    window.showFormErrors();

    const input = $('#title');
    const error = $('.form-field-error-message');
    expect(error).toHaveLength(1);
    expect(error.attr('role')).toBe('alert');
    expect(error.html()).toBe('<ul><li>Enter a title</li></ul>');
    expect(input.attr('aria-invalid')).toBe('true');
    expect(input.attr('aria-describedby').split(/\s+/)).toEqual(['title-help', 'title-error']);
  });
});
