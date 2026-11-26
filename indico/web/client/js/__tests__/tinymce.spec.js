// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import $ from 'jquery';
import tinymce from 'tinymce/tinymce';

import {getConfig} from '../tinymce';

jest.mock('tinymce/skins/content/default/content.css', () => '');
jest.mock('tinymce/skins/ui/oxide/content.css', () => '');

document.body.dataset.tinymceContentCss = '[]';

describe('getConfig', () => {
  it('appends extra style formats to the default ones', () => {
    const boxes = {title: 'Boxes', items: [{title: 'Box', block: 'div', wrapper: true}]};
    const {style_formats: defaultFormats} = getConfig(undefined);
    const {style_formats: formats} = getConfig(undefined, {extraStyleFormats: [boxes]});
    expect(formats).toEqual([...defaultFormats, boxes]);
  });
});

describe('legacy field', () => {
  beforeAll(() => {
    global.$ = $;
  });

  it('emits a single change event when leaving the editor', async () => {
    const field = document.createElement('textarea');
    document.body.appendChild(field);
    const onFieldChange = jest.fn();
    field.addEventListener('change', onFieldChange);
    const [editor] = await tinymce.init(getConfig(field));

    editor.getBody().innerHTML = '<p>new</p>';
    editor.dispatch('input');
    editor.dispatch('focusout');
    editor.dispatch('blur');
    await new Promise(resolve => setTimeout(resolve, 300));

    expect(onFieldChange).toHaveBeenCalledTimes(1);
    expect(field.value).toBe('<p>new</p>');
  });
});
