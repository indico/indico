// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global initForms */

import jQuery from 'jquery';

global.$ = global.jQuery = window.$ = window.jQuery = jQuery;

// the module runs on import, so it can only be loaded once jQuery is global
require('../forms'); // eslint-disable-line import/no-commonjs

function setupForm(widgetHtml = '') {
  document.body.innerHTML = `
    <form>
      <input type="text" name="title" value="">
      ${widgetHtml}
      <input type="submit" value="Save" data-disabled-until-change>
    </form>
  `;
  const form = $('form');
  initForms(form);
  return {form, submit: form.find(':submit')};
}

describe('initForms change tracking', () => {
  // let the module's own document-ready run before any test builds a form
  beforeAll(() => new Promise(resolve => setTimeout(resolve, 0)));

  it('keeps the submit button disabled while the form is untouched', () => {
    const {submit} = setupForm();

    expect(submit.prop('disabled')).toBe(true);
  });

  it('enables the submit button once a field changes', () => {
    const {form, submit} = setupForm();
    form.find('[name="title"]').val('new').trigger('change');

    expect(submit.prop('disabled')).toBe(false);
  });

  it('enables the submit button when a widget reports pending changes', () => {
    const {form, submit} = setupForm('<div class="widget" data-pending-changes></div>');
    form.trigger('change');

    expect(submit.prop('disabled')).toBe(false);
  });

  it('disables the submit button again once the widget has no pending changes', () => {
    const {form, submit} = setupForm('<div class="widget" data-pending-changes></div>');
    form.trigger('change');
    form.find('.widget').removeAttr('data-pending-changes');
    form.trigger('change');

    expect(submit.prop('disabled')).toBe(true);
  });
});
