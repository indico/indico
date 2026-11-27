// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global initForms */

import jQuery from 'jquery';

import 'indico/legacy/libs/presentation/Ui/Text';

import '../multiple_items_widget';

global.$ = global.jQuery = jQuery;
jQuery.fn.qtip = function() {
  return this;
};
global.repositionTooltips = () => {};

// the module runs on import, so it can only be loaded once jQuery is global
require('../../../utils/forms'); // eslint-disable-line import/no-commonjs

const COLUMNS = [
  {id: 'email', caption: 'Email', type: 'text', required: true},
  {id: 'lang', caption: 'Language', type: 'select', required: true},
];
const CHOICES = {lang: {en: 'English', fr: 'French'}};

function setupWidget(value = [], columns = COLUMNS) {
  document.body.innerHTML = `
    <form>
      <div class="form-group">
        <input type="hidden" id="items" name="items" value='${JSON.stringify(value)}'>
        <div id="items-widget" class="multiple-items-widget">
          <table class="i-table-widget"><tbody></tbody></table>
          <button type="button" id="items-add-button" class="js-add-row"></button>
        </div>
      </div>
      <input type="submit" value="Save" data-disabled-until-change>
    </form>
  `;
  window.setupMultipleItemsWidget({
    fieldId: 'items',
    uuidField: null,
    columns,
    sortable: false,
    columnChoices: CHOICES,
  });
  return {form: $('form'), field: $('#items'), widget: $('#items-widget')};
}

function fillRow(widget, index, values) {
  const inputs = widget.find('tbody > tr').eq(index).find('.js-table-input');
  values.forEach((value, i) => inputs.eq(i).val(value).trigger('change'));
}

function firstInput(widget, index = 0) {
  return widget.find('tbody > tr').eq(index).find('.js-table-input')[0];
}

describe('multiple items widget', () => {
  it('lets the form be submitted while the initial row is untouched', () => {
    const {form, widget} = setupWidget();

    expect(widget.find('tbody > tr')).toHaveLength(1);
    expect(form[0].checkValidity()).toBe(true);
  });

  it('blocks the submission while a row is being filled', () => {
    const {form, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);

    expect(form[0].checkValidity()).toBe(false);
    expect(firstInput(widget).validationMessage).toBe('Please save or cancel this row first.');
  });

  it('blocks the submission while a saved row is reopened for editing', () => {
    const {form, widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');

    expect(form[0].checkValidity()).toBe(false);
  });

  it('keeps blocking the submission when a reopened row is emptied', () => {
    const {form, widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');
    fillRow(widget, 0, ['', '']);

    expect(form[0].checkValidity()).toBe(false);
  });

  it('lets the form be submitted once the row is saved', () => {
    const {form, field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    widget.find('.js-save-row').trigger('click');

    expect(form[0].checkValidity()).toBe(true);
    expect(JSON.parse(field.val())).toEqual([{email: 'a@example.com', lang: 'en'}]);
  });

  it('lets the form be submitted once the edit is cancelled', () => {
    const {form, widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');
    widget.find('.js-cancel-edit').trigger('click');

    expect(form[0].checkValidity()).toBe(true);
  });

  it('lets the form be submitted once the unsaved row is discarded', () => {
    const {form, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    widget.find('.js-cancel-edit').trigger('click');

    expect(form[0].checkValidity()).toBe(true);
  });

  it('blocks the submission while a row holding only a checked checkbox is unsaved', () => {
    const columns = [
      {id: 'name', caption: 'Name', type: 'text'},
      {id: 'enabled', caption: 'Enabled', type: 'checkbox'},
    ];
    const {form, widget} = setupWidget([], columns);
    widget.find('.js-table-input').eq(1).prop('checked', true).trigger('change');

    expect(form[0].checkValidity()).toBe(false);
  });

  it('ignores a row whose inputs are disabled by a HiddenUnless toggle', () => {
    const {form, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    $('.form-group').find(':input').prop('disabled', true);

    expect(form[0].checkValidity()).toBe(true);
  });

  it('flags pending changes while a row is being filled', () => {
    const {widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);

    expect(widget.is('[data-pending-changes]')).toBe(true);
  });

  it('flags pending changes while a saved row is reopened', () => {
    const {widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');

    expect(widget.is('[data-pending-changes]')).toBe(true);
  });

  it('clears the pending flag once the row is saved', () => {
    const {widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    widget.find('.js-save-row').trigger('click');

    expect(widget.is('[data-pending-changes]')).toBe(false);
  });

  it('does not flag pending changes for the untouched initial row', () => {
    const {widget} = setupWidget();

    expect(widget.is('[data-pending-changes]')).toBe(false);
  });
});

describe('multiple items widget with form change tracking', () => {
  // let the forms module's own document-ready run before any test builds a form
  beforeAll(() => new Promise(resolve => $(resolve)));

  function setupTrackedWidget(value) {
    const {form, widget} = setupWidget(value);
    initForms(form);
    return {form, widget, submit: form.find(':submit')};
  }

  it('enables the submit button once a saved row is reopened', () => {
    const {form, widget, submit} = setupTrackedWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');

    expect(submit.prop('disabled')).toBe(false);
    expect(form.data('fieldsChanged')).toBe(true);
  });

  it.each([
    ['a changed edit is cancelled', ['b@example.com', 'fr'], '.js-cancel-edit', false],
    ['the row is saved unchanged', [], '.js-save-row', false],
    ['the row is saved with new values', ['b@example.com', 'fr'], '.js-save-row', true],
  ])('tracks the form change once %s', (desc, values, action, changed) => {
    const {form, widget, submit} = setupTrackedWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');
    fillRow(widget, 0, values);
    widget.find(action).trigger('click');

    expect(submit.prop('disabled')).toBe(!changed);
    expect(form.data('fieldsChanged')).toBe(changed);
  });
});
