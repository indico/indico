// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Clipboard from 'clipboard';

$(document).ready(function() {
  /* Show a qTip with the given text under the given element. The qTip is
   * destroyed when hidden and thus will be shown only once. */
  function showQTip(element, text, hideAfterDelay) {
    var $element = $(element);
    var container = $('<span>').qtip({
      overwrite: true,
      position: {
        target: $element,
      },
      content: {
        text: text,
      },
      hide: {
        event: 'unfocus click',
      },
      events: {
        hide: function() {
          $(this).qtip('destroy');
          $element.removeData('no-qtip');
        },
      },
    });
    $element.data('no-qtip', true).trigger('indico:closeAutoTooltip');
    container.qtip('show');

    if (hideAfterDelay) {
      setTimeout(function() {
        container.qtip('hide');
      }, 1000);
    }
  }

  /* Handle clicks on .js-copy-to-clipboard with clipboard.js.
   * For simple usage, the clipboard-text data attribute will be copied to
   * the system clipboard. For other possibilities, see https://clipboardjs.com/
   * */
  var c = new Clipboard('.js-copy-to-clipboard');
  c.on('success', function(evt) {
    showQTip(evt.trigger, $T.gettext('Copied to clipboard'), true);
  });
  c.on('error', function(evt) {
    var copyShortcut = 'CTRL-C';
    if (/^Mac/i.test(navigator.platform)) {
      copyShortcut = '⌘-C';
    }
    copyShortcut = '<strong>' + copyShortcut + '</strong>';
    showQTip(evt.trigger, $T.gettext('Press {0} to copy').format(copyShortcut));
  });

  /* Allow to use clipboard.js on <a> with href attributes. */
  $(document).on('click', '.js-copy-to-clipboard', function(evt) {
    evt.preventDefault();
  });
});
