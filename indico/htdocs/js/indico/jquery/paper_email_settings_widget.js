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

(function($) {
    'use strict';

    $.widget('indico.paperemailsettingswidget', {
        options: {
            containerElement: null,
            multipleRecipientOptions: [
                'notify_on_added_to_event', 'notify_on_assigned_contrib', 'notify_on_paper_submission'
            ],
            singleRecipientOptions: [
                'notify_judge_on_review', 'notify_author_on_judgment'
            ]
        },

        _initCheckboxes: function(data) {
            var self = this;
            var elementID = self.element.prop('id');
            var multipleRecipientOptions = self.options.multipleRecipientOptions;
            var singleRecipientOptions = self.options.singleRecipientOptions;

            multipleRecipientOptions.forEach(function(condition) {
                data[condition].forEach(function(role) {
                    $('#{0}-{1}-{2}'.format(elementID, condition, role)).prop('checked', true);
                });
            });
            singleRecipientOptions.forEach(function(condition) {
                $('#{0}-{1}'.format(elementID, condition)).prop('checked', data[condition]);
            });
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var $container = self.options.containerElement;
            var hiddenData = element.val() ? JSON.parse(element.val()) : {};

            self._initCheckboxes(hiddenData);

            $container.find('.multiple-recipients input').on('change', function() {
                var setting = hiddenData[this.name];
                if (this.checked) {
                    setting.push(this.value);
                } else {
                    setting.splice(setting.indexOf(this.value), 1);
                }
                element.val(JSON.stringify(hiddenData));
            });

            $container.find('.single-recipient input').on('change', function() {
                hiddenData[this.name] = this.checked;
                element.val(JSON.stringify(hiddenData));
            });
        }
    });
})(jQuery);
