// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const getConfig = ({images = false} = {}) => ({
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
      'underline',
      'strikethrough',
      '|',
      'link',
      'fontColor',
      'removeFormat',
      '|',
      'bulletedList',
      'numberedList',
      '-',
      'outdent',
      'indent',
      '|',
      images && 'imageInsert',
      'insertTable',
      '|',
      'subscript',
      'superscript',
      'blockQuote',
      'code',
      'horizontalLine',
      '|',
      'findAndReplace',
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
    'FontBackgroundColor',
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
    'Subscript',
    'Superscript',
    'Table',
    'TableToolbar',
    'Underline',
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
