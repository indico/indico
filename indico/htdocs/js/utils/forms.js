/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
            var value = checkedOnly ? conditionField.filter(':checked').val() : conditionField.val();
            var active = !!((requiredValue === null && value) || (requiredValue !== null && requiredValue === value));
            field.closest('.form-group').toggle(active);
            if (!field.is(':input')) {
                field.find(':input').prop('disabled', !active);
            } else {
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
        forms.find(':input[data-hidden-unless]').each(function() {
            var field = $(this);
            var data = field.data('hidden-unless');
            var conditionField = $(this.form).find(':input[name="{0}"]'.format(data.field));
            hideFieldUnless(field, conditionField, data.value, data.checked_only);
            (data.checked_only ? conditionField.filter(':checked') : conditionField).triggerHandler('change');
        });

        // track modifications
        forms.find('[data-disabled-until-change]').prop('disabled', true);
        forms.each(function() {
            var $this = $(this);
            $this.data('initialData', $this.serialize());
            $this.data('fieldsChanged', false);
        }).on('change input', function() {
            var $this = $(this);
            var untouched = $this.serialize() == $this.data('initialData');
            $this.find('[data-disabled-until-change]').prop('disabled', untouched);
            $this.closest('form').data('fieldsChanged', !untouched);
        });
    };

    global.aclIfProtected = function aclIfProtected(protectionField, aclField, selfProtection, inheritedProtection, folderField, folderProtection) {
        protectionField.on('change', function() {
            aclField.closest('.form-group')
                .find('input.i-button').prop('disabled', !this.checked).end()
                .find('.PluginOptionPeopleListDiv').toggleClass('disabled', !this.checked);
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

    $(document).ready(function() {
        initForms($('form'));
    });
})(window);
