// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global countWords:false */

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
    var $maxLengthInfo = $('#{0}-max-length-info'.format(options.fieldId));
    var value = $field.val().trim();
    $maxLengthInfo.empty();
    if (options.maxLength) {
      var charsLeft = options.maxLength - value.length;
      $('<span>', {
        html: $T
          .ngettext('<strong>1</strong> char left', '<strong>{0}</strong> chars left', charsLeft)
          .format(charsLeft),
        class: getLimitClass(charsLeft, options.maxLength),
      }).appendTo($maxLengthInfo);
    }
    if (options.maxWords) {
      var wordCount = countWords(value);
      var wordsLeft = options.maxWords - wordCount;
      $('<span>', {
        html: $T
          .ngettext('<strong>1</strong> word left', '<strong>{0}</strong> words left', wordsLeft)
          .format(wordsLeft),
        class: getLimitClass(wordsLeft, options.maxWords),
      }).appendTo($maxLengthInfo);
    }
  }

  function setupHelpTooltips($field) {
    var $container = $field.closest('[data-field-id]');
    ['markdown-info', 'latex-info', 'wmd-help-button'].forEach(function(name) {
      var content = $container.find('.{0}-text'.format(name));
      $container
        .find('.' + name)
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
        .on('click', function(evt) {
          evt.preventDefault();
        });
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
      var $field = $('#' + options.fieldId);
      $field.pagedown();

      if (options.maxLength || options.maxWords) {
        updateLimits($field, options);
        $field.on('change input', function() {
          updateLimits($(this), options);
        });
      }

      $field
        .on('focusin', function() {
          $field.parent().addClass('focused');
        })
        .on('focusout', function() {
          $field.parent().removeClass('focused');
        });

      setupHelpTooltips($field);
    }
  };
})(window);
