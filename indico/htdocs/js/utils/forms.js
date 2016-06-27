/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

(function(global) {
    'use strict';

    function validatePasswordConfirmation(passwordField, confirmField) {
        if ('setCustomValidity' in confirmField[0]) {
            passwordField.add(confirmField).on('change input', function() {
                if (passwordField.val() != confirmField.val()) {
                    confirmField[0].setCustomValidity($T('The passwords do not match.'));
                } else {
                    confirmField[0].setCustomValidity('');
                }
            });
        }
    }

    function hideFieldUnless(field, conditionField, requiredValue, checkedOnly) {
        conditionField.on('change', function() {
            var value = checkedOnly ? conditionField.filter(':checked').val() || false : conditionField.val();
            var active = !!((requiredValue === null && value) || (requiredValue !== null && requiredValue === value));
            field.closest('.form-group').toggle(active);
            if (!field.is(':input')) {
                field.find(':input').prop('disabled', !active);
            } else if(!field.data('initiallyDisabled')) {
                field.prop('disabled', !active);
            }
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
            hideFieldUnless(field, conditionField, data.value, data.checked_only);
            conditionField.triggerHandler('change');
        });

        // track modifications
        forms.find('[data-disabled-until-change]').prop('disabled', true);
        forms.each(function() {
            var $this = $(this);
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
            var untouched = $this.serialize() == $this.data('initialData');
            $this.find('[data-disabled-until-change]').prop('disabled', untouched);
            $this.closest('form').data('fieldsChanged', !untouched);
        });

        forms.find('fieldset.collapsible > legend').on('click', function(evt) {
            evt.preventDefault();
            var $this = $(this),
                collapseIcon = $this.find('div > span');
            $this.next('.fieldset-content').slideToggle();
            collapseIcon.toggleClass('icon-next icon-expand');
        });

        forms.find('fieldset.collapsible.initially-collapsed').each(function() {
            var $this = $(this);
            if ($this.find('div.form-field[data-error]').length) {
                $this.find('legend').trigger('click');
            }
        });
    };

    global.toggleAclField = function toogleAclField(aclField, state) {
        aclField.closest('.form-group')
                .find('input.i-button').prop('disabled', state).end()
                .find('a.i-button').toggleClass('disabled', state).end()
                .find('.PluginOptionPeopleListDiv').toggleClass('disabled', state);
    };

    global.aclIfProtected = function aclIfProtected(protectionField, aclField, selfProtection, inheritedProtection, folderField, folderProtection) {
        protectionField.on('change', function() {
            toggleAclField(aclField, !this.checked);

            if (selfProtection && inheritedProtection) {
                selfProtection.toggle(this.checked);
                inheritedProtection.toggle(!this.checked);
                if (folderField) {
                    folderField.triggerHandler('change');
                }
                else {
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

    global.messageIfFolderProtected = function messageIfFolderProtected(protectionField, folderField, protectionInfo, selfProtection, inheritedProtection, folderProtection) {
        folderField.on('change', function() {
            var selectedFolder = $(this);
            if (protectionInfo[selectedFolder.val()] && !protectionField.prop('checked')) {
                selfProtection.hide();
                inheritedProtection.hide();
                folderProtection.find('.folder-name').html(selectedFolder.children('option:selected').text());
                folderProtection.show();
            }
            else {
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
     * - extraCheckCallback: Function called with the checkboxes as argument. If it returns false the buttons will be disabled.
     */
    global.enableIfChecked = function enableIfChecked(checkboxContainer, checkboxSelector, buttonSelector, extraCheckCallback) {
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

            if (numRows === options.totalRows || numChecked < numRows) {
                // only one page or not everything selected
                messageContainer.hide();
                _setAllSelected(false);
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

    $(document).ready(function() {
        initForms($('form'));
    });
})(window);
