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

(function() {
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

    $(document).ready(function() {
        $('form input[data-confirm-password]').each(function() {
            var confirmField = $(this);
            var passwordField = $(this.form).find('input[name="' + confirmField.data('confirmPassword') + '"]');
            validatePasswordConfirmation(passwordField, confirmField);
        });

        var disabled_until_change_buttons = $('form [data-disabled-until-change]');
        disabled_until_change_buttons.closest('form').each(function() {
            $(this).data('serialized', $(this).serialize());
        }).on('change input', function() {
            var untouched = $(this).serialize() == $(this).data('serialized');
            disabled_until_change_buttons.prop('disabled', untouched);
        }).end().prop('disabled', true);
    });
})();
