// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global initForms */

import jQuery from 'jquery';

global.$ = global.jQuery = jQuery;

// the modules run on import, so they can only be loaded once jQuery is global
require('../misc'); // eslint-disable-line import/no-commonjs
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
  beforeAll(() => new Promise(resolve => $(resolve)));

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

describe('initForms save reminder', () => {
  beforeAll(() => new Promise(resolve => $(resolve)));

  function setupReminderForm(title) {
    document.body.innerHTML = `
      <form>
        <input type="text" name="title" value="${title}" required>
        <input type="text" name="notes" value="">
        <input type="submit" value="Save" data-disabled-until-change data-save-reminder>
      </form>
    `;
    // jsdom has no layout, so the save button is moved out of view to get the reminder shown
    const button = $('[data-save-reminder]')[0];
    button.getClientRects = () => [{}];
    button.getBoundingClientRect = () => ({top: 10000, left: 0, bottom: 10000, right: 0});
    const form = $('form');
    const onSubmit = jest.fn(evt => evt.preventDefault());
    initForms(form);
    form.on('submit', onSubmit);
    form.find('[name="notes"]').val('changed').trigger('change');
    return {onSubmit, saveNow: () => $('.save-corner-message .corner-message-action')};
  }

  it('submits the form when it is valid', () => {
    const {onSubmit, saveNow} = setupReminderForm('Title');
    saveNow().trigger('click');

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('keeps offering to save instead of submitting an invalid form', () => {
    const {onSubmit, saveNow} = setupReminderForm('');
    saveNow().trigger('click');

    expect(onSubmit).not.toHaveBeenCalled();
    expect(saveNow()).toHaveLength(1);
  });
});
