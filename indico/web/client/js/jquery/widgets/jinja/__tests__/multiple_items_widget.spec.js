// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import jQuery from 'jquery';

import 'indico/legacy/libs/presentation/Ui/Text';

import '../multiple_items_widget';

global.$ = global.jQuery = window.$ = window.jQuery = jQuery;
jQuery.fn.qtip = function() {
  return this;
};
global.repositionTooltips = () => {};

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
  values.forEach((value, i) => inputs.eq(i).val(value));
}

function pressEnter(widget, index) {
  const input = widget.find('tbody > tr').eq(index).find('input.js-table-input').first();
  input.trigger($.Event('keypress', {keyCode: 13}));
}

// mirrors how jquery-form announces a serialization it can still be told to skip
function submitAjax(form) {
  const veto = {};
  form.trigger('form-pre-serialize', [form, {}, veto]);
  return !veto.veto;
}

describe('multiple items widget', () => {
  it('commits a filled pending row before the form is serialized', () => {
    const {form, field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);

    expect(submitAjax(form)).toBe(true);
    expect(JSON.parse(field.val())).toEqual([{email: 'a@example.com', lang: 'en'}]);
  });

  it('commits a pending row that is being edited alongside committed ones', () => {
    const {form, field, widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-add-row').trigger('click');
    fillRow(widget, 1, ['b@example.com', 'fr']);

    expect(submitAjax(form)).toBe(true);
    expect(JSON.parse(field.val())).toEqual([
      {email: 'a@example.com', lang: 'en'},
      {email: 'b@example.com', lang: 'fr'},
    ]);
  });

  it('commits a row that was reopened for editing', () => {
    const {form, field, widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');
    fillRow(widget, 0, ['changed@example.com', 'fr']);

    expect(submitAjax(form)).toBe(true);
    expect(JSON.parse(field.val())).toEqual([{email: 'changed@example.com', lang: 'fr'}]);
  });

  it('drops the untouched empty row instead of blocking the submission', () => {
    const {form, field, widget} = setupWidget();

    expect(widget.find('tbody > tr')).toHaveLength(1);
    expect(submitAjax(form)).toBe(true);
    expect(JSON.parse(field.val())).toEqual([]);
  });

  it('keeps an editable row when another field blocks the submission', () => {
    const {form, widget} = setupWidget();

    submitAjax(form);
    expect(widget.find('tbody > tr .js-table-input')).toHaveLength(2);
  });

  it('vetoes the serialization when a pending row is missing a required value', () => {
    const {form, field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', '']);

    expect(submitAjax(form)).toBe(false);
    expect(JSON.parse(field.val())).toEqual([]);
    expect(widget.find('tbody > tr .js-table-input')).toHaveLength(2);
  });

  it('ignores the widget when the field is disabled by a HiddenUnless toggle', () => {
    const {form, field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', '']);
    $('.form-group').find(':input').prop('disabled', true);

    expect(submitAjax(form)).toBe(true);
    expect(JSON.parse(field.val())).toEqual([]);
  });

  it('commits a filled pending row on a plain form submission', () => {
    const {form, field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);

    form.trigger('submit');
    expect(JSON.parse(field.val())).toEqual([{email: 'a@example.com', lang: 'en'}]);
  });

  it('commits the pending row before adding another one', () => {
    const {field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    widget.find('.js-add-row').trigger('click');

    expect(JSON.parse(field.val())).toEqual([{email: 'a@example.com', lang: 'en'}]);
    expect(widget.find('tbody > tr')).toHaveLength(2);
  });

  it('refuses to add another row while the pending one is incomplete', () => {
    const {widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', '']);
    widget.find('.js-add-row').trigger('click');

    expect(widget.find('tbody > tr')).toHaveLength(1);
  });

  it('never accumulates blank rows when adding repeatedly', () => {
    const {widget} = setupWidget();
    widget.find('.js-add-row').trigger('click');
    widget.find('.js-add-row').trigger('click');

    expect(widget.find('tbody > tr')).toHaveLength(1);
  });

  it('flags pending changes while a row is being filled', () => {
    const {widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', '']);
    widget.find('.js-table-input').eq(0).trigger('change');

    expect(widget.is('[data-pending-changes]')).toBe(true);
  });

  it('flags pending changes while a committed row is reopened', () => {
    const {widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');

    expect(widget.is('[data-pending-changes]')).toBe(true);
  });

  it('clears the pending flag once the row is committed', () => {
    const {widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    widget.find('.js-table-input').eq(0).trigger('change');
    pressEnter(widget, 0);

    expect(widget.is('[data-pending-changes]')).toBe(false);
  });

  it('offers no per-row save button', () => {
    const {widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');

    expect(widget.find('.js-save-row')).toHaveLength(0);
    expect(widget.find('.js-cancel-edit')).toHaveLength(1);
  });

  it('commits a row when enter is pressed in it', () => {
    const {field, widget} = setupWidget();
    fillRow(widget, 0, ['a@example.com', 'en']);
    pressEnter(widget, 0);

    expect(JSON.parse(field.val())).toEqual([{email: 'a@example.com', lang: 'en'}]);
  });

  it('clears the pending flag when the edit is cancelled', () => {
    const {widget} = setupWidget([{email: 'a@example.com', lang: 'en'}]);
    widget.find('.js-edit-row').trigger('click');
    widget.find('.js-cancel-edit').trigger('click');

    expect(widget.is('[data-pending-changes]')).toBe(false);
  });

  it('does not flag pending changes for the untouched empty row', () => {
    const {widget} = setupWidget();

    expect(widget.is('[data-pending-changes]')).toBe(false);
  });

  it('keeps a row holding only a checked checkbox', () => {
    const columns = [
      {id: 'name', caption: 'Name', type: 'text'},
      {id: 'enabled', caption: 'Enabled', type: 'checkbox'},
    ];
    const {form, field, widget} = setupWidget([], columns);
    widget.find('tbody > tr .js-table-input').eq(1).prop('checked', true);

    expect(submitAjax(form)).toBe(true);
    expect(JSON.parse(field.val())).toEqual([{name: '', enabled: true}]);
  });
});
