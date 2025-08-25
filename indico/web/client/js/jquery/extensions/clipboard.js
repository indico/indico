// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Clipboard from 'clipboard';

import {$T} from 'indico/utils/i18n';

$(document).ready(() => {
  /* Show a qTip with the given text under the given element. The qTip is
   * destroyed when hidden and thus will be shown only once. */
  function showQTip(element, text, hideAfterDelay) {
    const $element = $(element);
    const container = $('<span>').qtip({
      overwrite: true,
      position: {
        target: $element,
      },
      content: {
        text,
      },
      hide: {
        event: 'unfocus click',
      },
      events: {
        hide() {
          $(this).qtip('destroy');
          $element.removeData('no-qtip');
        },
      },
    });
    $element.data('no-qtip', true).trigger('indico:closeAutoTooltip');
    container.qtip('show');

    if (hideAfterDelay) {
      setTimeout(() => {
        container.qtip('hide');
      }, 1000);
    }
  }

  /* Handle clicks on .js-copy-to-clipboard with clipboard.js.
   * For simple usage, the clipboard-text data attribute will be copied to
   * the system clipboard. For other possibilities, see https://clipboardjs.com/
   * */
  const c = new Clipboard('.js-copy-to-clipboard');
  c.on('success', evt => {
    showQTip(evt.trigger, $T.gettext('Copied to clipboard'), true);
  });
  c.on('error', evt => {
    let copyShortcut = 'CTRL-C';
    if (/^Mac/i.test(navigator.platform)) {
      copyShortcut = '⌘-C';
    }
    copyShortcut = `<strong>${copyShortcut}</strong>`;
    showQTip(evt.trigger, $T.gettext('Press {0} to copy').format(copyShortcut));
  });

  /* Allow to use clipboard.js on <a> with href attributes. */
  $(document).on('click', '.js-copy-to-clipboard', evt => {
    evt.preventDefault();
  });
});
