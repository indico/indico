// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global countWords:false, initForms:false, showFormErrors:false, toggleAclField:false */

// eslint-disable-next-line import/unambiguous

import {Translate} from 'indico/react/i18n';

(function(global) {
  function validatePasswordConfirmation(passwordField, confirmField) {
    if ('setCustomValidity' in confirmField[0]) {
      passwordField.add(confirmField).on('change input', function() {
        if (passwordField.val() !== confirmField.val()) {
          confirmField[0].setCustomValidity($T('The passwords do not match.'));
        } else {
          confirmField[0].setCustomValidity('');
        }
      });
    }
  }

  function hideFieldUnless(field, conditionField, requiredValues, checkedOnly) {
    conditionField.on('change', function() {
      const value = checkedOnly
        ? conditionField.filter(':checked').val() || false
        : conditionField.val();
      const active = !!(
        (!requiredValues.length && value) ||
        (requiredValues.length && _.contains(requiredValues, value))
      );
      field.closest('.form-group').toggle(active);
      let realField = field.is(':input') ? field : field.find(':input');
      if (realField.attr('type') === 'hidden') {
        // in case of custom widgets with multiple fields (e.g. the new react-based
        // date/time field) we need to select all inputs explicitly since the hidden
        // field is rather meaningless and the non-hidden fields break the form if they
        // are visually hidden but not actually disabled
        realField = field.closest('.form-group').find(':input');
      }
      if (realField.length && !field.data('initiallyDisabled')) {
        realField.prop('disabled', !active);
      }
    });
  }

  function validateLength($field) {
    if (!('setCustomValidity' in $field[0])) {
      return;
    }

    const minChars = $field.data('min-length');
    const maxChars = $field.data('max-length');
    const minWords = $field.data('min-words');
    const maxWords = $field.data('max-words');

    $field.on('change input', function() {
      let msg = '';
      const charCount = $field.val().trim().length;
      const wordCount = countWords($field.val());

      if ((minChars && charCount < minChars) || (maxChars && charCount > maxChars)) {
        if (!maxChars) {
          msg = $T
            .ngettext(
              'Field must be at least {0} character long.',
              'Field must be at least {0} characters long.',
              minChars
            )
            .format(minChars);
        } else if (!minChars) {
          msg = $T
            .ngettext(
              'Field cannot be longer than {0} character.',
              'Field cannot be longer than {0} characters.',
              maxChars
            )
            .format(maxChars);
        } else {
          msg = $T
            .gettext('Field must be between {0} and {1} characters long.')
            .format(minChars, maxChars);
        }
      } else if ((minWords && wordCount < minWords) || (maxWords && wordCount > maxWords)) {
        if (!maxWords) {
          msg = $T
            .ngettext(
              'Field must contain at least {0} word.',
              'Field must contain at least {0} words.',
              minWords
            )
            .format(minWords);
        } else if (!minWords) {
          msg = $T
            .ngettext(
              'Field cannot contain more than {0} word.',
              'Field cannot contain more than {0} words.',
              maxWords
            )
            .format(maxWords);
        } else {
          msg = $T
            .gettext('Field must contain between {0} and {1} words.')
            .format(minWords, maxWords);
        }
      }
      $field[0].setCustomValidity(msg);
    });
  }

  function isElementInView(elem) {
    const docViewTop = $(window).scrollTop();
    const docViewBottom = docViewTop + $(window).height();
    const elemTop = $(elem).offset().top;
    const elemBottom = elemTop + $(elem).height();
    return elemBottom <= docViewBottom && elemTop >= docViewTop;
  }

  function showSaveCornerMessage($form) {
    cornerMessage({
      actionLabel: $T.gettext('Save now'),
      progressMessage: $T.gettext('Saving...'),
      message: $T.gettext('Do not forget to save your changes!'),
      class: 'highlight save-corner-message',
      actionCallback() {
        $form.submit();
      },
    });
  }

  function hideSaveCornerMessage($cornerMessage) {
    $cornerMessage.fadeOut(300, function() {
      $cornerMessage.remove();
    });
  }

  global.initForms = function initForms(forms) {
    // ConfirmPassword validator
    forms.find('input[data-confirm-password]').each(function() {
      const confirmField = $(this);
      const confirmFieldName = confirmField.data('confirmPassword');
      const passwordField = $(this.form).find(`input[name="${confirmFieldName}"]`);
      validatePasswordConfirmation(passwordField, confirmField);
    });

    // HiddenUnless validator
    forms.find(':input[data-hidden-unless]:disabled').data('initiallyDisabled', true);
    forms.find(':input[data-hidden-unless]').each(function() {
      const field = $(this);
      const data = field.data('hidden-unless');
      const conditionField = $(this.form).find(':input[name="{0}"]'.format(data.field));
      hideFieldUnless(field, conditionField, data.values, data.checked_only);
      setTimeout(() => {
        // we defer this call since react-based fields may no have fully rendered yet,
        // so if we call it too early we end up disabling only the hidden fields but
        // not the actual inputs in the react field (which is a problem e.g. in case
        // of the WTFDateTimeField).
        conditionField.triggerHandler('change');
      }, 0);
    });

    // SoftLength/WordCount validators
    const selectors = '[data-min-words], [data-max-words], [data-min-length], [data-max-length]';
    forms
      .find('input, textarea')
      .filter(selectors)
      .each(function() {
        validateLength($(this));
      });

    // track modifications
    forms.find('[data-disabled-until-change]').prop('disabled', true);
    forms
      .each(function() {
        const $this = $(this);

        if ($this.data('initialized')) {
          console.warn('re-initialized form', this); // eslint-disable-line no-console
        }
        $this.data('initialized', true);

        function _resetData() {
          $this.data('initialData', $.param($this.serializeArray(), true));
          $this.data('fieldsChanged', false);
        }
        _resetData();

        $this.on('indico:fieldsSaved', function() {
          _resetData();
          $this.find('[data-disabled-until-change]').prop('disabled', true);
        });

        if ($this.data('confirm-close-unsaved') !== undefined) {
          const oldOnBeforeUnload = window.onbeforeunload;
          window.onbeforeunload = () =>
            $this.data('fieldsChanged')
              ? Translate.string('Are you sure you want to leave this page without saving?')
              : undefined;
          $this.on('submit', () => {
            window.onbeforeunload = oldOnBeforeUnload;
          });
        }
      })
      .on('change input', function() {
        const $this = $(this);
        const untouched = $.param($this.serializeArray(), true) === $this.data('initialData');
        const $cornerMessage = $('.save-corner-message');
        $this.find('[data-disabled-until-change]').prop('disabled', untouched);
        $this.closest('form').data('fieldsChanged', !untouched);
        if ($this.find('[data-save-reminder]').length && !$this.data('locked-event-disabled')) {
          if (
            !isElementInView($this.find('[data-save-reminder]')) &&
            !untouched &&
            !$cornerMessage.length
          ) {
            showSaveCornerMessage($this);
          } else if (untouched) {
            hideSaveCornerMessage($cornerMessage);
          }
        }
      });

    // Remove corner message when 'Save' button is visible on screen
    $(window)
      .off('scroll.initForms')
      .on(
        'scroll.initForms',
        _.debounce(function() {
          const $form = forms.find('[data-save-reminder]').closest('form');
          if ($form.length) {
            const $cornerMessage = $('.save-corner-message');
            const untouched = $.param($form.serializeArray(), true) === $form.data('initialData');
            if (isElementInView($form.find('[data-save-reminder]'))) {
              hideSaveCornerMessage($cornerMessage);
            } else if (!untouched && !$cornerMessage.length) {
              showSaveCornerMessage($form);
            }
          }
        }, 100)
      );

    forms.find('fieldset.collapsible > legend').on('click', function(evt) {
      evt.preventDefault();
      const $this = $(this);
      const $collapseIcon = $this.find('div > span');
      $this.next('.fieldset-content').slideToggle();
      $collapseIcon.toggleClass('icon-next icon-expand');
    });

    forms.find('fieldset.collapsible.initially-collapsed').each(function() {
      const $this = $(this);
      if ($this.find('div.form-field[data-error]').length) {
        $this.find('legend').trigger('click');
      }
    });

    if (forms.closest('.event-locked').length) {
      const lockedForms = forms.filter('.disable-fields-if-locked');
      lockedForms.data('locked-event-disabled', true);
      lockedForms.find(':input:not([type=hidden]):not([data-button-back])').prop('disabled', true);
      lockedForms.find(':input:submit').hide();
    }
  };

  global.toggleAclField = function toggleAclField(aclField, state) {
    aclField
      .closest('.form-group')
      .find('input.i-button')
      .prop('disabled', state)
      .end()
      .find('a.i-button')
      .toggleClass('disabled', state)
      .end();
  };

  global.aclIfProtected = function aclIfProtected(
    protectionField,
    aclField,
    selfProtection,
    inheritedProtection,
    folderField,
    folderProtection
  ) {
    protectionField.on('change', function() {
      if (aclField) {
        toggleAclField(aclField, !this.checked);
      } else {
        selfProtection.addClass('no-acl-field');
      }

      if (selfProtection && inheritedProtection) {
        selfProtection.toggle(this.checked);
        inheritedProtection.toggle(!this.checked);
        if (folderField) {
          folderField.triggerHandler('change');
        } else {
          folderProtection.hide();
        }
      }
    });
    _.defer(function() {
      protectionField.triggerHandler('change');
      if (folderField) {
        folderField.triggerHandler('change');
      }
    });
  };

  global.messageIfFolderProtected = function messageIfFolderProtected(
    protectionField,
    folderField,
    protectionInfo,
    selfProtection,
    inheritedProtection,
    folderProtection
  ) {
    folderField.on('change', function() {
      const selectedFolder = $(this);
      if (protectionInfo[selectedFolder.val()] && !protectionField.prop('checked')) {
        selfProtection.hide();
        inheritedProtection.hide();
        folderProtection
          .find('.folder-name')
          .html(selectedFolder.children('option:selected').text());
        folderProtection.show();
      } else {
        folderProtection.hide();
        selfProtection.toggle(protectionField.prop('checked'));
        inheritedProtection.toggle(!protectionField.prop('checked'));
      }
    });
    _.defer(function() {
      folderField.triggerHandler('change');
    });
  };

  /* Enable or disable elements (typically buttons) based on the state of checkboxes.
   *
   * - checkboxContainer: Element or jQuery object containing the checkboxes to consider
   * - checkboxSelector: Selector to find the checkboxes inside the containers
   * - buttonSelector: Selector, jQuery object or element corresponding to the button(s) to be enabled/disabled
   * - extraCheckCallback: Function called with the checkboxes as argument.
   *                       If it returns false the buttons will be disabled.
   */
  global.enableIfChecked = function enableIfChecked(
    checkboxContainer,
    checkboxSelector,
    buttonSelector,
    extraCheckCallback
  ) {
    function _update(force) {
      const $checkboxes = $(checkboxContainer)
        .find(checkboxSelector)
        .filter(':checked');
      let checked = force || !!$checkboxes.length;
      if (extraCheckCallback && extraCheckCallback($checkboxes) === false) {
        checked = false;
      }
      $(buttonSelector)
        .prop('disabled', !checked)
        .toggleClass('disabled', !checked);
    }

    $(checkboxContainer)
      .on('change', checkboxSelector, function() {
        _update(this.checked);
      })
      .on('indico:syncEnableIfChecked', function() {
        _update();
      });

    _update();
  };

  /* Provide a "select really everything" option for paginated lists.
   * When selecting all rows in such a list a message is shown indicating
   * that only the current page is selected with the option to select all
   * items (no matter on which page).
   */
  global.paginatedSelectAll = function paginatedSelectAll(options) {
    options = $.extend(
      true,
      {
        // the container element used as context for all other selectors.
        // in case of dynamically updated rows, this must remain the same
        // all the time as events are bound to it
        containerSelector: null,
        // the selector for the row selection checkboxes. used within the
        // context of containerSelector
        checkboxSelector: null,
        // the selector for the (usually hidden) all-items-on-all-pages-selected
        // checkbox. used within the context of containerSelector
        allSelectedSelector: null,
        // the selector for the element where the message whether all items
        // on the current page or really all items are selected.
        // used within the global context, i.e. not restricted by the given
        // containerSelector.
        selectionMessageSelector: null,
        // the total number of rows. may also be a function.
        totalRows: 0,
        messages: {
          // message shown when all items on all pages are selected
          allSelected(total) {
            // never used with total == 1. empty string is invalid so we use `*` instead
            return $T.ngettext('*', 'All {0} rows are currently selected.').format(total);
          },
          // message shown when all items on the current page are selected
          pageSelected(selected, total) {
            // never used with total == 1
            return $T
              .ngettext(
                'Only {0} out of {1} rows is currently selected',
                'Only {0} out of {1} rows are currently selected.',
                selected
              )
              .format(selected, total);
          },
        },
      },
      options
    );

    const container = $(options.containerSelector);
    container.on('change', options.checkboxSelector, _update);
    _update();

    function _update() {
      const messageContainer = $(options.selectionMessageSelector).empty();
      const numChecked = container.find(`${options.checkboxSelector}:checked`).length;
      const numUnchecked = container.find(`${options.checkboxSelector}:not(:checked)`).length;
      const numRows = numChecked + numUnchecked;

      if (numChecked < numRows) {
        // not everything selected
        messageContainer.hide();
        _setAllSelected(false);
      } else if (numChecked === options.totalRows) {
        // everything selected and only one page
        messageContainer.hide();
        _setAllSelected(true);
      } else if (numChecked === numRows) {
        // all rows selected
        if (_getAllSelected()) {
          $('<span>', {
            html: options.messages.allSelected(options.totalRows),
          }).appendTo(messageContainer);
          messageContainer.append(' ');
          $('<a>', {
            href: '#',
            text: $T.gettext('Select only the current page.'),
            click(evt) {
              evt.preventDefault();
              _setAllSelected(false);
              _update();
            },
          }).appendTo(messageContainer);
        } else {
          $('<span>', {
            html: options.messages.pageSelected(numChecked, options.totalRows),
          }).appendTo(messageContainer);
          messageContainer.append(' ');
          $('<a>', {
            href: '#',
            text: $T.gettext('Click here to select them all.'),
            click(evt) {
              evt.preventDefault();
              _setAllSelected(true);
              _update();
            },
          }).appendTo(messageContainer);
        }
        messageContainer.show();
      }
    }

    function _getAllSelected() {
      return container.find(options.allSelectedSelector).prop('checked');
    }

    function _setAllSelected(selected) {
      container
        .find(options.allSelectedSelector)
        .prop('checked', selected)
        .trigger('change');
    }

    return {
      isEverythingSelected: _getAllSelected,
    };
  };

  global.getDropzoneFiles = function getDropzoneFiles($form) {
    const files = {};
    const dropzoneField = $form.data('dropzoneField');
    if (dropzoneField) {
      files[dropzoneField.id] = $form[0].dropzone.getUploadingFiles();
    }
    return files;
  };

  const DROPZONE_FILE_KEYS = [
    'upload',
    'status',
    'previewElement',
    'previewTemplate',
    '_removeLink',
    'accepted',
    'width',
    'height',
    'processing',
    'xhr',
  ];

  global.setDropzoneFiles = function setDropzoneFiles($field, files) {
    const dropzone = $field.closest('form')[0].dropzone;
    _.defer(function() {
      files.forEach(function(file) {
        DROPZONE_FILE_KEYS.forEach(function(key) {
          delete file[key];
        });
        dropzone.addFile(file);
      });
    });
  };

  $(document).ready(function() {
    initForms($('form'));

    $('body').on('indico:htmlUpdated', function(evt) {
      const $target = $(evt.target);
      const $forms = $target.find('form');
      if ($forms.length) {
        initForms($forms);
        showFormErrors($target);
      }
    });
  });
})(window);
