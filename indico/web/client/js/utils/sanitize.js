// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _sanitizeHtml from 'sanitize-html';

/* eslint array-element-newline: off */

// The following are whitelisted tags, attributes & CSS styles for
// sanitizing HTML provided by the user, such as when pasting into the WYSIWYG editor.
// It is the same configuration that is used by bleach on the server-side (except for the legacy attributes).
// See 'indico/util/string.py'

// biome-ignore format: keep block compact
const ALLOWED_TAGS = [
  // bleach.ALLOWED_TAGS
  'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul',
  // BLEACH_ALLOWED_TAGS
  'sup', 'sub', 'small', 'br', 'p', 'table', 'thead', 'tbody', 'th', 'tr', 'td', 'img', 'hr', 'h1', 'h2', 'h3', 'h4',
  'h5', 'h6', 'pre', 'dl', 'dd', 'dt', 'figure', 'blockquote',
  // BLEACH_ALLOWED_TAGS_HTML
  'address', 'area', 'bdo', 'big', 'caption', 'center', 'cite', 'col', 'colgroup', 'del', 'dfn', 'dir', 'div',
  'fieldset', 'font', 'ins', 'kbd', 'legend', 'map', 'menu', 'q', 's', 'samp', 'span', 'strike', 'tfoot', 'tt', 'u',
  'var'
];

const ALLOWED_ATTRIBUTES = {
  '*': ['style'],
  // bleach.ALLOWED_ATTRIBUTES
  a: ['href', 'title'],
  abbr: ['title'],
  acronym: ['title'],
  // BLEACH_ALLOWED_ATTRIBUTES
  img: ['src', 'alt', 'style'],
};

// biome-ignore format: keep block compact
const ALLOWED_STYLES = [
  'background-color', 'border-top-color', 'border-top-style', 'border-top-width', 'border-top', 'border-right-color',
  'border-right-style', 'border-right-width', 'border-right', 'border-bottom-color', 'border-bottom-style',
  'border-bottom-width', 'border-bottom', 'border-left-color', 'border-left-style', 'border-left-width',
  'border-left', 'border-color', 'border-style', 'border-width', 'border', 'bottom', 'border-collapse',
  'border-spacing', 'color', 'clear', 'clip', 'caption-side', 'display', 'direction', 'empty-cells', 'float',
  'font-size', 'font-family', 'font-style', 'font', 'font-variant', 'font-weight', 'font-size-adjust', 'font-stretch',
  'height', 'left', 'list-style-type', 'list-style-position', 'line-height', 'letter-spacing', 'marker-offset',
  'margin', 'margin-left', 'margin-right', 'margin-top', 'margin-bottom', 'max-height', 'min-height', 'max-width',
  'min-width', 'marks', 'overflow', 'outline-color', 'outline-style', 'outline-width', 'outline', 'orphans',
  'position', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left', 'padding', 'page', 'page-break-after',
  'page-break-before', 'page-break-inside', 'quotes', 'right', 'size', 'text-align', 'top', 'table-layout',
  'text-decoration', 'text-indent', 'text-shadow', 'text-transform', 'unicode-bidi', 'visibility', 'vertical-align',
  'width', 'widows', 'white-space', 'word-spacing', 'word-wrap', 'z-index'
]

// Sanitize user-provided HTML, such as when pasting into ckeditor.
export function sanitizeHtml(dirty) {
  const matchAny = /^.*$/;
  const allowedStyles = ALLOWED_STYLES.reduce((styles, name) => {
    styles[name] = [matchAny];
    return styles;
  }, {});

  return _sanitizeHtml(dirty, {
    allowedTags: ALLOWED_TAGS,
    allowedAttributes: ALLOWED_ATTRIBUTES,
    allowedStyles,
    allowedSchemesByTag: {
      // blob and data are needed for TinyMCE image pasting:
      // - blob is used when image uploading is enabled (uploading and replacing with a URL happens
      //   at a later step)
      // - data is used when it'd disabled: the editor will remove the pasted image and if data
      //   urls weren't enabled, the pasted image would be sanitized to `<img />` which is broken
      //   but no longer removed by the editor
      img: ['http', 'https', 'blob', 'data'],
    },
  });
}
