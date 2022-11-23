// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {sanitizeHtml} from './utils/sanitize';

export const getConfig = ({
  images = true,
  imageUploadURL = null,
  fullScreen = true,
  showToolbar = true,
} = {}) => ({
  removePlugins: images && imageUploadURL ? [] : ['ImageInsert', 'ImageUpload'],
  fontFamily: {
    options: [
      'Sans Serif/"Liberation Sans", sans-serif',
      'Serif/"Liberation Serif", serif',
      'Monospace/"Liberation Mono", monospace',
    ],
  },
  toolbar: showToolbar && {
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
      'fontBackgroundColor',
      'removeFormat',
      '|',
      'bulletedList',
      'numberedList',
      'alignment',
      'outdent',
      'indent',
      '|',
      images && 'insertImage',
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
      fullScreen && 'fullscreen',
      fullScreen && '|',
      'sourceEditing',
    ].filter(Boolean),
  },
  plugins: [
    'Alignment',
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
    fullScreen && 'FullScreen',
    'GeneralHtmlSupport',
    'Heading',
    'HorizontalLine',
    images && 'Image',
    images && 'ImageBlockEditing',
    images && 'ImageCaption',
    images && 'ImageEditing',
    images && !imageUploadURL && 'ImageInsertViaUrl',
    images && imageUploadURL && 'ImageInsert',
    images && 'ImageResize',
    images && 'ImageStyle',
    images && 'ImageToolbar',
    images && 'ImageUtils',
    'Indent',
    'IndentBlock',
    'Italic',
    'Link',
    images && 'LinkImage',
    'List',
    images && 'MediaEmbed',
    'Paragraph',
    'PasteFromOffice',
    'RemoveFormat',
    images && imageUploadURL && 'SimpleUploadAdapter',
    'SourceEditing',
    'Strikethrough',
    'Subscript',
    'Superscript',
    'Table',
    'TableToolbar',
    'TableProperties',
    'TableCellProperties',
    'Underline',
  ].filter(Boolean),
  table: {
    contentToolbar: [
      'tableColumn',
      'tableRow',
      'mergeTableCells',
      'tableProperties',
      'tableCellProperties',
    ],
  },
  htmlSupport: {
    allow: [
      {name: /^h[1-6]$/, styles: true, classes: true},
      {name: 'p', styles: true, classes: true},
      {name: 'dl', styles: true, classes: true},
      {name: 'dt', styles: true, classes: true},
      {name: 'dd', styles: true, classes: true},
      {name: 'div', styles: true, classes: true},
      {name: 'span', styles: true, classes: true},
      {name: 'pre', styles: true, classes: true},
      {
        name: 'img',
        attributes: {
          usemap: true,
        },
        styles: true,
        classes: true,
      },
      {
        name: 'area',
        attributes: true,
        styles: true,
        classes: true,
      },
      {
        name: 'map',
        attributes: true,
        styles: true,
        classes: true,
      },
    ],
  },
  link: {
    decorators: {
      openInNewTab: {
        mode: 'manual',
        label: 'Open in a new tab',
        defaultValue: false,
        attributes: {
          target: '_blank',
          rel: 'noopener noreferrer',
        },
      },
    },
  },
  image: {
    toolbar: [
      'imageTextAlternative',
      'imageStyle:inline',
      'imageStyle:block',
      'imageStyle:side',
      'imageStyle:alignLeft',
      'imageStyle:alignRight',
      '|',
      'linkImage',
    ],
  },
  simpleUpload:
    images && imageUploadURL
      ? {
          uploadUrl: imageUploadURL,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-Token': document.getElementById('csrf-token').getAttribute('content'),
          },
        }
      : undefined,
});

// Sanitize HTML pasted into ckeditor.
// Use it with the clipboardInput event and pass the editor instance:
//
//   editor.editing.view.document.on('clipboardInput', sanitizeHtmlOnPaste(editor))
//
// More info: https://ckeditor.com/docs/ckeditor5/latest/framework/guides/deep-dive/clipboard.html
export function sanitizeHtmlOnPaste(editor) {
  return (ev, data) => {
    if (data.method !== 'paste' || data.content) {
      return;
    }
    const dataTransfer = data.dataTransfer;
    const contentData = dataTransfer.getData('text/html');
    if (contentData) {
      data.content = editor.data.htmlProcessor.toView(sanitizeHtml(contentData));
    }
  };
}
