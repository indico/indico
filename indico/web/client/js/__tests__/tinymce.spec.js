// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'tinymce/tinymce';

import {getConfig} from '../tinymce';

jest.mock('tinymce/skins/content/default/content.css', () => '');
jest.mock('tinymce/skins/ui/oxide/content.css', () => '');

describe('getConfig', () => {
  it('appends extra style formats to the default ones', () => {
    const boxes = {title: 'Boxes', items: [{title: 'Box', block: 'div', wrapper: true}]};
    const {style_formats: defaultFormats} = getConfig(undefined);
    const {style_formats: formats} = getConfig(undefined, {extraStyleFormats: [boxes]});
    expect(formats).toEqual([...defaultFormats, boxes]);
  });
});
