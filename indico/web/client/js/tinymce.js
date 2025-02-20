// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import contentStyles from 'tinymce/skins/content/default/content.css';
import contentUIStyles from 'tinymce/skins/ui/oxide/content.css';

import 'tinymce/models/dom/model';
import 'tinymce/themes/silver';
import 'tinymce/icons/default';
import 'tinymce/skins/ui/oxide/skin.min.css';
// import 'tinymce/plugins/advlist';
// import 'tinymce/plugins/anchor';
// import 'tinymce/plugins/autolink';
// import 'tinymce/plugins/autoresize';
// import 'tinymce/plugins/autosave';
// import 'tinymce/plugins/charmap';
import 'tinymce/plugins/code';
import 'tinymce/plugins/codesample';
// import 'tinymce/plugins/directionality';
import 'tinymce/plugins/fullscreen';
// import 'tinymce/plugins/help';
import 'tinymce/plugins/image';
// import 'tinymce/plugins/importcss';
// import 'tinymce/plugins/insertdatetime';
import 'tinymce/plugins/link';
import 'tinymce/plugins/lists';
// import 'tinymce/plugins/media';
// import 'tinymce/plugins/nonbreaking';
// import 'tinymce/plugins/pagebreak';
// import 'tinymce/plugins/preview';
import 'tinymce/plugins/quickbars';
// import 'tinymce/plugins/save';
import 'tinymce/plugins/searchreplace';
import 'tinymce/plugins/table';
// import 'tinymce/plugins/template';
// import 'tinymce/plugins/visualblocks';
// import 'tinymce/plugins/visualchars';
// import 'tinymce/plugins/wordcount';

import {indicoAxios, handleAxiosError} from './utils/axios';
import {sanitizeHtml} from './utils/sanitize';
import './prism';

const extraContentCSS = `
body {
  height: initial;
}
`;

export const getConfig = (
  field,
  {
    images = true,
    imageUploadURL = null,
    fullScreen = true,
    showToolbar = true,
    forceAbsoluteURLs = false,
    contentCSS = [],
    height = 475,
  } = {},
  {onChange = null} = {}
) => ({
  target: field,
  promotion: false,
  branding: false,
  plugins: [
    'code',
    'codesample',
    'fullscreen',
    'image',
    'link',
    'lists',
    'quickbars',
    'searchreplace',
    'table',
  ],
  height,
  skin: false,
  body_class: 'editor-output',
  content_css: contentCSS,
  content_style: `${contentUIStyles.toString()}\n${contentStyles.toString()}\n${extraContentCSS}`,
  text_patterns: [
    {start: '*', end: '*', format: 'italic'},
    {start: '**', end: '**', format: 'bold'},
    {start: '~~', end: '~~', format: 'strikethrough'},
    {start: '==', end: '==', format: 'mark'},
    {start: '`', end: '`', format: 'code'},
    {start: '#', format: 'h1'},
    {start: '##', format: 'h2'},
    {start: '###', format: 'h3'},
    {start: '####', format: 'h4'},
    {start: '#####', format: 'h5'},
    {start: '######', format: 'h6'},
    {start: '1. ', cmd: 'InsertOrderedList'},
    {start: '* ', cmd: 'InsertUnorderedList'},
    {start: '- ', cmd: 'InsertUnorderedList'},
  ],
  formats: {
    mark: {inline: 'mark'},
  },
  // This is the default, with "Mark" added to the list.
  // https://www.tiny.cloud/docs/tinymce/latest/user-formatting-options/#style_formats
  style_formats: [
    {
      title: 'Headings',
      items: [
        {title: 'Heading 1', format: 'h1'},
        {title: 'Heading 2', format: 'h2'},
        {title: 'Heading 3', format: 'h3'},
        {title: 'Heading 4', format: 'h4'},
        {title: 'Heading 5', format: 'h5'},
        {title: 'Heading 6', format: 'h6'},
      ],
    },
    {
      title: 'Inline',
      items: [
        {title: 'Bold', format: 'bold'},
        {title: 'Italic', format: 'italic'},
        {title: 'Underline', format: 'underline'},
        {title: 'Strikethrough', format: 'strikethrough'},
        {title: 'Mark', format: 'mark'},
        {title: 'Superscript', format: 'superscript'},
        {title: 'Subscript', format: 'subscript'},
        {title: 'Code', format: 'code'},
      ],
    },
    {
      title: 'Blocks',
      items: [
        {title: 'Paragraph', format: 'p'},
        {title: 'Blockquote', format: 'blockquote'},
        {title: 'Div', format: 'div'},
        {title: 'Pre', format: 'pre'},
      ],
    },
    {
      title: 'Align',
      items: [
        {title: 'Left', format: 'alignleft'},
        {title: 'Center', format: 'aligncenter'},
        {title: 'Right', format: 'alignright'},
        {title: 'Justify', format: 'alignjustify'},
      ],
    },
  ],
  codesample_global_prismjs: true,
  codesample_languages: [
    {text: 'Text', value: 'none'},
    {text: 'Bash', value: 'bash'},
    {text: 'C', value: 'c'},
    {text: 'C++', value: 'cpp'},
    {text: 'C#', value: 'csharp'},
    {text: 'CSS', value: 'css'},
    {text: 'CSV', value: 'csv'},
    {text: 'Diff', value: 'diff'},
    {text: 'Docker', value: 'docker'},
    {text: 'Fortran', value: 'fortran'},
    {text: 'Go', value: 'go'},
    {text: 'Java', value: 'java'},
    {text: 'JSON', value: 'json'},
    {text: 'React JSX', value: 'jsx'},
    {text: 'Julia', value: 'julia'},
    {text: 'LaTeX', value: 'latex'},
    {text: 'LUA', value: 'lua'},
    {text: 'MATLAB', value: 'matlab'},
    {text: 'HTML/XML', value: 'markup'},
    {text: 'PERL', value: 'perl'},
    {text: 'PHP', value: 'php'},
    {text: 'PowerShell', value: 'powershell'},
    {text: 'Python', value: 'python'},
    {text: 'R', value: 'r'},
    {text: 'Ruby', value: 'ruby'},
    {text: 'Rust', value: 'rust'},
    {text: 'SQL', value: 'sql'},
    {text: 'TypeScript', value: 'typescript'},
    {text: 'YAML', value: 'yaml'},
  ],
  quickbars_insert_toolbar: false,
  menubar: false,
  statusbar: showToolbar,
  toolbar_mode: 'wrap',
  toolbar: !showToolbar
    ? false
    : [
        'styles',
        '|',
        'bold',
        'italic',
        'underline',
        'strikethrough',
        'mark',
        'removeformat',
        '|',
        'link',
        'forecolor',
        'backcolor',
        '|',
        'bullist',
        'numlist',
        'outdent',
        'indent',
        '|',
        images && 'image',
        'table',
        '|',
        'subscript',
        'superscript',
        'blockquote',
        'codesample',
        'hr',
        '|',
        'searchreplace',
        'undo',
        'redo',
        '|',
        fullScreen && 'fullscreen',
        'code',
      ]
        .filter(x => x)
        .join(' '),
  entity_encoding: 'raw',
  convert_unsafe_embeds: true,
  sandbox_iframes: true,
  relative_urls: false, // kind of misleading: this just ensures domain-relative URLs
  remove_script_host: !forceAbsoluteURLs, // this ensures fully absolute (`https://....`) URLs
  end_container_on_empty_block: true,
  paste_data_images: images && !!imageUploadURL,
  images_reuse_filename: true,
  image_uploadtab: images && !!imageUploadURL,
  images_upload_handler: async (blobInfo, progress) => {
    const formData = new FormData();
    formData.append('upload', blobInfo.blob(), blobInfo.filename());

    try {
      const {data} = await indicoAxios.post(imageUploadURL, formData, {
        headers: {'content-type': 'multipart/form-data'},
        onUploadProgress: ({loaded, total}) => progress((loaded / total) * 100),
      });
      progress(100);
      return data.url;
    } catch (error) {
      if (_.get(error, 'response.status') !== 422) {
        const msg = handleAxiosError(error);
        // eslint-disable-next-line no-throw-literal
        throw {message: `Upload failed: ${msg}`, remove: true};
      }
      // eslint-disable-next-line no-throw-literal
      throw {message: 'Upload failed', remove: true};
    }
  },
  smart_paste: false,
  paste_preprocess: (editor, args) => {
    args.content = sanitizeHtml(args.content);
  },
  setup: editor => {
    editor.ui.registry.addButton('mark', {
      tooltip: 'Mark',
      icon: 'permanent-pen',
      onAction() {
        editor.formatter.toggle('mark');
      },
    });

    // auto-save to hidden field (or trigger change event) on input
    editor.on(
      'change input compositionend setcontent CommentChange',
      _.debounce(
        () => {
          if (field) {
            editor.save();
            editor.targetElm.dispatchEvent(new Event('change', {bubbles: true}));
          } else if (onChange) {
            onChange(editor);
          }
        },
        200,
        // XXX if you touch this make sure it remains shorter than rollback in the react component
        {maxWait: 1000}
      )
    );

    if (field) {
      editor.on('init', () => {
        // Re-position the dialog if we have one since the initial position is
        // wrong due to the editor being loaded after the dialog has been opened.
        const dialog = $(field.closest('.ui-dialog-content'));
        if (dialog.length) {
          dialog.dialog('option', 'position', dialog.dialog('option', 'position'));
        }
        // Make sure the option dropdowns are displayed above the dialog.
        const uiDialog = field.closest('.ui-dialog-content');
        const exPopup = field.closest('.exclusivePopup');
        if (uiDialog) {
          uiDialog.style.overflow = 'inherit';
        }
        if (exPopup) {
          exPopup.style.overflow = 'inherit';
        }
      });
    }
  },
});
