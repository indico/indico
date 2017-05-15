/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

/* global countWords:false, initForms:false, showFormErrors:false, toggleAclField:false */

(function(global) {
    'use strict';

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
            var value = checkedOnly ? conditionField.filter(':checked').val() || false : conditionField.val();
            var active = !!((!requiredValues.length && value) ||
                            (requiredValues.length && _.contains(requiredValues, value)));
            field.closest('.form-group').toggle(active);
            var realField = field.is(':input') ? field : field.find(':input');
            if (realField.length) {
                // Selectize clones the field and copies the `required` flag so we need
                // to make sure to also disable the clone to avoid validation errors!
                var selectizeField = realField[0].selectize ? $('#{0}-selectized'.format(realField[0].id)) : $();
                if (!field.data('initiallyDisabled')) {
                    realField.prop('disabled', !active);
                    selectizeField.prop('disabled', !active);
                }
            }
        });
    }

    function validateLength($field) {
        if (!('setCustomValidity' in $field[0])) {
            return;
        }

        var minChars = $field.data('min-length');
        var maxChars = $field.data('max-length');
        var minWords = $field.data('min-words');
        var maxWords = $field.data('max-words');

        $field.on('change input', function() {
            var msg = '';
            var charCount = $field.val().trim().length;
            var wordCount = countWords($field.val());

            if ((minChars && charCount < minChars) || (maxChars && charCount > maxChars)) {
                if (!maxChars) {
                    msg = $T.ngettext('Field must be at least {0} character long.',
                                      'Field must be at least {0} characters long.', minChars).format(minChars);
                } else if (!minChars) {
                    msg = $T.ngettext('Field cannot be longer than {0} character.',
                                      'Field cannot be longer than {0} characters.', maxChars).format(maxChars);
                } else {
                    msg = $T.gettext('Field must be between {0} and {1} characters long.').format(minChars, maxChars);
                }
            } else if ((minWords && wordCount < minWords) || (maxWords && wordCount > maxWords)) {
                if (!maxWords) {
                    msg = $T.ngettext('Field must contain at least {0} word.',
                                      'Field must contain at least {0} words.', minWords).format(minWords);
                } else if (!minWords) {
                    msg = $T.ngettext('Field cannot contain more than {0} word.',
                                      'Field cannot contain more than {0} words.', maxWords).format(maxWords);
                } else {
                    msg = $T.gettext('Field must contain between {0} and {1} words.').format(minWords, maxWords);
                }
            }
            $field[0].setCustomValidity(msg);
        });
    }

    function isElementInView(elem) {
        var docViewTop = $(window).scrollTop();
        var docViewBottom = docViewTop + $(window).height();
        var elemTop = $(elem).offset().top;
        var elemBottom = elemTop + $(elem).height();
        return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
    }

    function showSaveCornerMessage($form) {
        cornerMessage({
            actionLabel: $T.gettext('Save now'),
            progressMessage: $T.gettext('Saving...'),
            message: $T.gettext('Do not forget to save your changes!'),
            class: 'highlight save-corner-message',
            actionCallback: function() {
                $form.submit();
            }
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
            var confirmField = $(this);
            var passwordField = $(this.form).find('input[name="' + confirmField.data('confirmPassword') + '"]');
            validatePasswordConfirmation(passwordField, confirmField);
        });

        // HiddenUnless validator
        forms.find(':input[data-hidden-unless]:disabled').data('initiallyDisabled', true);
        forms.find(':input[data-hidden-unless]').each(function() {
            var field = $(this);
            var data = field.data('hidden-unless');
            var conditionField = $(this.form).find(':input[name="{0}"]'.format(data.field));
            hideFieldUnless(field, conditionField, data.values, data.checked_only);
            conditionField.triggerHandler('change');
        });

        // SoftLength/WordCount validators
        var selectors = '[data-min-words], [data-max-words], [data-min-length], [data-max-length]';
        forms.find('input, textarea').filter(selectors).each(function() {
            validateLength($(this));
        });

        // track modifications
        forms.find('[data-disabled-until-change]').prop('disabled', true);
        forms.each(function() {
            var $this = $(this);

            if ($this.data('initialized')) {
                console.warn('re-initialized form', this);  // eslint-disable-line no-console
            }
            $this.data('initialized', true);

            function _resetData() {
                $this.data('initialData', $this.serialize());
                $this.data('fieldsChanged', false);
            }
            _resetData();

            $this.on('indico:fieldsSaved', function() {
                _resetData();
                $this.find('[data-disabled-until-change]').prop('disabled', true);
            });
        }).on('change input', function() {
            var $this = $(this);
            var untouched = $this.serialize() === $this.data('initialData');
            var $cornerMessage = $('.save-corner-message');
            $this.find('[data-disabled-until-change]').prop('disabled', untouched);
            $this.closest('form').data('fieldsChanged', !untouched);
            if ($this.find('[data-save-reminder]').length && !$this.data('locked-event-disabled')) {
                if (!isElementInView($this.find('[data-save-reminder]'))
                    && !untouched && !$cornerMessage.length) {
                    showSaveCornerMessage($this);
                } else if (untouched) {
                    hideSaveCornerMessage($cornerMessage);
                }
            }
        });

        // Remove corner message when 'Save' button is visible on screen
        $(window).off('scroll.initForms').on('scroll.initForms', _.debounce(function() {
            var $form = forms.find('[data-save-reminder]').closest('form');
            if ($form.length) {
                var $cornerMessage = $('.save-corner-message');
                var untouched = $form.serialize() === $form.data('initialData');
                if (isElementInView($form.find('[data-save-reminder]'))) {
                    hideSaveCornerMessage($cornerMessage);
                } else if (!untouched && !$cornerMessage.length) {
                    showSaveCornerMessage($form);
                }
            }
        }, 100));

        forms.find('fieldset.collapsible > legend').on('click', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var $collapseIcon = $this.find('div > span');
            $this.next('.fieldset-content').slideToggle();
            $collapseIcon.toggleClass('icon-next icon-expand');
        });

        forms.find('fieldset.collapsible.initially-collapsed').each(function() {
            var $this = $(this);
            if ($this.find('div.form-field[data-error]').length) {
                $this.find('legend').trigger('click');
            }
        });

        if (forms.closest('.event-locked').length) {
            var lockedForms = forms.filter('.disable-fields-if-locked');
            lockedForms.data('locked-event-disabled', true);
            lockedForms.find(':input:not([type=hidden]):not([data-button-back])').prop('disabled', true);
            lockedForms.find(':input:submit').hide();
        }
    };

    global.toggleAclField = function toogleAclField(aclField, state) {
        aclField.closest('.form-group')
                .find('input.i-button').prop('disabled', state).end()
                .find('a.i-button').toggleClass('disabled', state).end()
                .find('.PluginOptionPeopleListDiv').toggleClass('disabled', state);
    };

    global.aclIfProtected = function aclIfProtected(protectionField, aclField, selfProtection, inheritedProtection,
                                                    folderField, folderProtection) {
        protectionField.on('change', function() {
            toggleAclField(aclField, !this.checked);

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

    global.messageIfFolderProtected = function messageIfFolderProtected(protectionField, folderField, protectionInfo,
                                                                        selfProtection, inheritedProtection,
                                                                        folderProtection) {
        folderField.on('change', function() {
            var selectedFolder = $(this);
            if (protectionInfo[selectedFolder.val()] && !protectionField.prop('checked')) {
                selfProtection.hide();
                inheritedProtection.hide();
                folderProtection.find('.folder-name').html(selectedFolder.children('option:selected').text());
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
    global.enableIfChecked = function enableIfChecked(checkboxContainer, checkboxSelector, buttonSelector,
                                                      extraCheckCallback) {
        function _update(force) {
            var $checkboxes = $(checkboxContainer).find(checkboxSelector).filter(':checked');
            var checked = force || !!$checkboxes.length;
            if (extraCheckCallback && extraCheckCallback($checkboxes) === false) {
                checked = false;
            }
            $(buttonSelector).prop('disabled', !checked).toggleClass('disabled', !checked);
        }

        $(checkboxContainer).on('change', checkboxSelector, function() {
            _update(this.checked);
        }).on('indico:syncEnableIfChecked', function() {
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
        options = $.extend(true, {
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
                allSelected: function(total) {
                    // never used with total == 1. empty string is invalid so we use `*` instead
                    return $T.ngettext('*', 'All {0} rows are currently selected.').format(total);
                },
                // message shown when all items on the current page are selected
                pageSelected: function(selected, total) {
                    // never used with total == 1
                    return $T.ngettext('Only {0} out of {1} rows is currently selected',
                                       'Only {0} out of {1} rows are currently selected.',
                                       selected).format(selected, total);
                }
            }
        }, options);

        var container = $(options.containerSelector);
        container.on('change', options.checkboxSelector, _update);
        _update();

        function _update() {
            var messageContainer = $(options.selectionMessageSelector).empty();
            var numChecked = container.find(options.checkboxSelector + ':checked').length;
            var numUnchecked = container.find(options.checkboxSelector + ':not(:checked)').length;
            var numRows = numChecked + numUnchecked;

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
                        html: options.messages.allSelected(options.totalRows)
                    }).appendTo(messageContainer);
                    messageContainer.append(' ');
                    $('<a>', {
                        href: '#',
                        text: $T.gettext('Select only the current page.'),
                        click: function(evt) {
                            evt.preventDefault();
                            _setAllSelected(false);
                            _update();
                        }
                    }).appendTo(messageContainer);
                } else {
                    $('<span>', {
                        html: options.messages.pageSelected(numChecked, options.totalRows)
                    }).appendTo(messageContainer);
                    messageContainer.append(' ');
                    $('<a>', {
                        href: '#',
                        text: $T.gettext('Click here to select them all.'),
                        click: function(evt) {
                            evt.preventDefault();
                            _setAllSelected(true);
                            _update();
                        }
                    }).appendTo(messageContainer);
                }
                messageContainer.show();
            }
        }

        function _getAllSelected() {
            return container.find(options.allSelectedSelector).prop('checked');
        }

        function _setAllSelected(selected) {
            container.find(options.allSelectedSelector).prop('checked', selected).trigger('change');
        }

        return {
            isEverythingSelected: _getAllSelected
        };
    };

    global.getDropzoneFiles = function getDropzoneFiles($form) {
        var files = {};
        var dropzoneField = $form.data('dropzoneField');
        if (dropzoneField) {
            files[dropzoneField.id] = $form[0].dropzone.getUploadingFiles();
        }
        return files;
    };

    var DROPZONE_FILE_KEYS = [
        'upload', 'status', 'previewElement', 'previewTemplate', '_removeLink',
        'accepted', 'width', 'height', 'processing', 'xhr'
    ];

    global.setDropzoneFiles = function setDropzoneFiles($field, files) {
        var dropzone = $field.closest('form')[0].dropzone;
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
            var $target = $(evt.target);
            var $forms = $target.find('form');
            if ($forms.length) {
                initForms($forms);
                showFormErrors($target);
            }
        });
    });
})(window);
