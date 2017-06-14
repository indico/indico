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

$(document).ready(function() {
    'use strict';

    // Header shrinking function
    $(window).scroll(function() {
        if (($(window).scrollTop() >= $('.bootstrap-header').outerHeight() / 2) &&
                !$('.bootstrap-header').hasClass('mini')) {
            $('.bootstrap-header').addClass('mini');
            $('.bootstrap-body').addClass('mini');
            $(window).scrollTop(0);
        }
    });

    // Instance Tracking slider
    $('#form-group-enable_tracking .switch-input').on('change', function() {
        var $this = $(this);
        var enabled = $this.prop('checked');
        var itEmail = $('#contact_email');
        var itContact = $('#contact_name');
        var firstName = $('#first_name').val();
        var lastName = $('#last_name').val();
        var name = (!!firstName && !!lastName) ? '{0} {1}'.format(firstName, lastName) : '';

        itEmail.prop('required', enabled);
        itEmail.prop('disabled', !enabled);
        if (!itEmail.val()) {
            itEmail.val($('#email').val());
            itEmail.trigger('input');
        }
        itContact.prop('required', enabled);
        itContact.prop('disabled', !enabled);
        if (!itContact.val() && !!name) {
            itContact.val(name);
            itContact.trigger('input');
        }
    });
    $('#form-group-enable_tracking .switch-input').trigger('change');
});
