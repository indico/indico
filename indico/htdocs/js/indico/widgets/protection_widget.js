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

(function(global) {
    'use strict';

    global.setupProtectionWidget = function setupProtectionWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            fieldName: null,
            parentProtected: false,
            aclFieldId: null,
            aclMessageUrl: null,
            hasInheritedAcl: false
        }, options);

        var inputs = $('input[name=' + options.fieldName + '][id^=' + options.fieldId + ']');
        var $enableAclLink = $('.enable-acl-link');
        var $aclListField = $('.acl-list-field');

        inputs.on('change', function() {
            var $this = $(this);
            var isProtected = $this.val() === 'protected' || ($this.val() === 'inheriting' && options.parentProtected);

            if (this.checked) {
                $('#form-group-protected-{0} .protection-message'.format(options.fieldId)).hide();
                $('#form-group-protected-{0} .{1}-protection-message'.format(options.fieldId, $this.val())).show();

                if (options.aclMessageUrl && options.hasInheritedAcl) {
                    $.ajax({
                        url: options.aclMessageUrl,
                        data: {mode: $this.val()},
                        error: handleAjaxError,
                        success: function(data) {
                            $this.closest('form').find('.inheriting-acl-message').html(data.html);
                        }
                    });
                }
                $aclListField.toggleClass('hidden', !isProtected);
                $enableAclLink.toggleClass('hidden', isProtected);
            }
        });

        $enableAclLink.on('click', function(evt) {
            evt.preventDefault();
            $('input[name=' + options.fieldName + '][value="protected"]').trigger('click');
        });

        _.defer(function() {
            inputs.trigger('change');
        });
    };
})(window);
