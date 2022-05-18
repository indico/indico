// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './ckeditor.css';

export const getConfig = ({simple = true, images = false} = {}) => ({
  language: 'en_GB',
  fontFamily: {
    options: [
      'Sans Serif/"Liberation Sans", sans-serif',
      'Serif/"Liberation Serif", serif',
      'Monospace/"Liberation Mono", monospace',
    ],
  },
  toolbar: {
    shouldNotGroupWhenFull: false,
    items: [
      'heading',
      '|',
      'bold',
      'italic',
      'strikethrough',
      '|',
      'fontColor',
      'removeFormat',
      '|',
      'bulletedList',
      'numberedList',
      'outdent',
      'indent',
      '|',
      'link',
      !simple && images && 'imageInsert',
      !simple && 'insertTable',
      '|',
      !simple && 'blockQuote',
      !simple && 'code',
      !simple && 'horizontalLine',
      '|',
      !simple && 'findAndReplace',
      'undo',
      'redo',
      '|',
      'sourceEditing',
    ].filter(Boolean),
  },
  plugins: [
    'Autoformat',
    images && 'AutoImage',
    'AutoLink',
    'BlockQuote',
    'Bold',
    'CloudServices',
    'Code',
    'CodeBlock',
    'Essentials',
    'FindAndReplace',
    'FontColor',
    'GeneralHtmlSupport',
    'Heading',
    'HorizontalLine',
    images && 'Image',
    images && 'ImageCaption',
    images && 'ImageInsert',
    images && 'ImageStyle',
    images && 'ImageToolbar',
    // images && 'ImageUpload',
    'Indent',
    'IndentBlock',
    'Italic',
    'Link',
    'List',
    images && 'MediaEmbed',
    'Paragraph',
    'PasteFromOffice',
    'RemoveFormat',
    'SourceEditing',
    'Strikethrough',
    'Table',
    'TableToolbar',
  ].filter(Boolean),
  htmlSupport: {
    allow: [
      {name: 'dl'},
      {name: 'dt'},
      {name: 'dd'},
      {name: 'div'},
      {name: 'span'},
      {name: 'pre'},
      {
        name: 'img',
        attributes: {
          usemap: true,
        },
      },
      {
        name: 'area',
        attributes: true,
      },
      {
        name: 'map',
        attributes: true,
      },
    ],
  },
});
