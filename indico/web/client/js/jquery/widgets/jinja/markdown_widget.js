// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {$T} from 'indico/utils/i18n';

/* global countWords */

(function(global) {
  function getLimitClass(remaining, max) {
    if (remaining < 0) {
      return 'limit-exceeded';
    } else if (remaining <= max * 0.2) {
      return 'limit-close';
    } else {
      return '';
    }
  }

  function updateLimits($field, options) {
    const $maxLengthInfo = $('#{0}-max-length-info'.format(options.fieldId));
    const value = $field.val().trim();
    $maxLengthInfo.empty();
    if (options.maxLength) {
      const charsLeft = options.maxLength - value.length;
      $('<span>', {
        html: $T
          .ngettext('<strong>1</strong> char left', '<strong>{0}</strong> chars left', charsLeft)
          .format(charsLeft),
        class: getLimitClass(charsLeft, options.maxLength),
      }).appendTo($maxLengthInfo);
    }
    if (options.maxWords) {
      const wordCount = countWords(value);
      const wordsLeft = options.maxWords - wordCount;
      $('<span>', {
        html: $T
          .ngettext('<strong>1</strong> word left', '<strong>{0}</strong> words left', wordsLeft)
          .format(wordsLeft),
        class: getLimitClass(wordsLeft, options.maxWords),
      }).appendTo($maxLengthInfo);
    }
  }

  function setupHelpTooltips($field) {
    const $container = $field.closest('[data-field-id]');
    ['markdown-info', 'latex-info', 'wmd-help-button'].forEach(name => {
      const content = $container.find('.{0}-text'.format(name));
      $container
        .find(`.${name}`)
        .qtip({
          content: content.html(),
          hide: {
            event: 'unfocus',
          },
          show: {
            solo: true,
          },
          style: {
            classes: 'informational markdown-help-qtip',
          },
        })
        .on('click', evt => {
          evt.preventDefault();
        });
    });
  }

  function setupAccessibleToolbar($field) {
    const $container = $field.closest('[data-field-id]');
    const $buttonRow = $container.find('.wmd-button-row');
    if (!$buttonRow.length) {
      return;
    }

    $buttonRow.attr({
      role: 'toolbar',
      'aria-label': $T.gettext('Formatting'),
    });

    $buttonRow.find('li.wmd-spacer').attr('aria-hidden', 'true');

    const isMac = /mac|iphone|ipad|ipod/i.test(navigator.platform);
    const buttonConfig = {
      bold: {label: $T.gettext('Bold'), shortcut: 'Ctrl+B'},
      italic: {label: $T.gettext('Italic'), shortcut: 'Ctrl+I'},
      link: {label: $T.gettext('Insert link'), shortcut: 'Ctrl+L'},
      quote: {label: $T.gettext('Quote'), shortcut: 'Ctrl+Q'},
      code: {label: $T.gettext('Code'), shortcut: 'Ctrl+K'},
      image: {label: $T.gettext('Insert image'), shortcut: 'Ctrl+G'},
      olist: {label: $T.gettext('Numbered list'), shortcut: 'Ctrl+O'},
      ulist: {label: $T.gettext('Bulleted list'), shortcut: 'Ctrl+U'},
      heading: {label: $T.gettext('Heading'), shortcut: 'Ctrl+H'},
      hr: {label: $T.gettext('Horizontal rule'), shortcut: 'Ctrl+R'},
      undo: {label: $T.gettext('Undo'), shortcut: 'Ctrl+Z'},
      redo: {label: $T.gettext('Redo'), shortcut: isMac ? 'Ctrl+Shift+Z' : 'Ctrl+Y'},
    };

    $buttonRow.find('li.wmd-button').each((_, li) => {
      const $li = $(li);
      const isHelp = $li.hasClass('wmd-help-button');
      const id = li.id;
      const match = id.match(/^wmd-(\w+)-button/);
      const action = match ? match[1] : null;

      const iconSpan = li.querySelector('span');

      const button = document.createElement('button');
      button.type = 'button';
      button.className = li.className;
      button.id = id;
      li.removeAttribute('id');
      li.removeAttribute('title');
      li.removeAttribute('style');
      li.className = 'wmd-button-item';

      if (iconSpan) {
        button.appendChild(iconSpan);
      }

      if (isHelp) {
        const label = document.createElement('span');
        label.className = 'text-label';
        label.textContent = $T.gettext('Markdown editing help');
        button.appendChild(label);
        li.appendChild(button);
      } else if (action && buttonConfig[action]) {
        const config = buttonConfig[action];
        const tipContent = document.createElement('span');
        tipContent.setAttribute('data-tip-content', '');
        tipContent.textContent = `${config.label} (${config.shortcut})`;
        button.appendChild(tipContent);

        const tooltip = document.createElement('ind-with-tooltip');
        tooltip.appendChild(button);
        li.appendChild(tooltip);
      } else {
        li.appendChild(button);
      }
    });
  }

  global.setupMarkdownWidget = function setupMarkdownWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        useMarkdownEditor: false,
        maxLength: 0,
        maxWords: 0,
      },
      options
    );

    if (options.useMarkdownEditor) {
      const $field = $(`#${options.fieldId}`);
      $field.pagedown();
      setupAccessibleToolbar($field);

      // The editor doesn't trigger any input/change events when applying changes via keyboard
      // shortcuts or the button bar, so we need to manually take care of this to enable submit
      // buttons etc.
      const $container = $field.closest('[data-field-id]');
      const textarea = $container.find('textarea.wmd-input')[0];
      $container.find('.wmd-button-bar').on('click', () => {
        textarea.dispatchEvent(new Event('change', {bubbles: true}));
      });
      textarea.addEventListener('keydown', evt => {
        if (evt.ctrlKey) {
          textarea.dispatchEvent(new Event('change', {bubbles: true}));
        }
      });

      if (options.maxLength || options.maxWords) {
        updateLimits($field, options);
        $field.on('change input', function() {
          updateLimits($(this), options);
        });
      }

      $field
        .on('focusin', () => {
          $field.parent().addClass('focused');
        })
        .on('focusout', () => {
          $field.parent().removeClass('focused');
        });

      setupHelpTooltips($field);
    }
  };
})(window);
