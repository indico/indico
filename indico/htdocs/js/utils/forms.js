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

(function(globals) {
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

    globals.initForms = function initForms(forms) {
        forms.find('input[data-confirm-password]').each(function() {
            var confirmField = $(this);
            var passwordField = $(this.form).find('input[name="' + confirmField.data('confirmPassword') + '"]');
            validatePasswordConfirmation(passwordField, confirmField);
        });

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

    $(document).ready(function() {
        initForms($('form'));
    });
})(window);
