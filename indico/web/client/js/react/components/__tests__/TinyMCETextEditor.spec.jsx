// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {act, render, waitFor} from '@testing-library/react';
import React from 'react';
import {Form} from 'react-final-form';
import tinymce from 'tinymce/tinymce';

import {FinalTinyMCETextEditor} from '../TinyMCETextEditor';

jest.mock('tinymce/skins/content/default/content.css', () => '');
jest.mock('tinymce/skins/ui/oxide/content.css', () => '');

document.body.dataset.tinymceContentCss = '[]';

describe('FinalTinyMCETextEditor', () => {
  it('keeps an edit made right before leaving the editor', async () => {
    let formValues;
    render(
      <Form onSubmit={() => {}} initialValues={{text: '<p>old</p>'}}>
        {({values}) => {
          formValues = values;
          return <FinalTinyMCETextEditor name="text" />;
        }}
      </Form>
    );
    await waitFor(() => expect(tinymce.activeEditor?.initialized).toBe(true));
    const editor = tinymce.activeEditor;

    // leave the editor before the debounced change handler had a chance to run; the
    // browser fires `focusout` on the editor body first, then TinyMCE's own `blur`
    act(() => {
      editor.getBody().innerHTML = '<p>new</p>';
      editor.dispatch('input');
      editor.dispatch('focusout');
      editor.dispatch('blur');
    });

    expect(editor.getContent()).toBe('<p>new</p>');
    expect(formValues.text).toBe('<p>new</p>');
  });
});
