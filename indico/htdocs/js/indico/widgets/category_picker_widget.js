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

    global.setupCategoryPickerWidget = function setupCategoryPickerWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            navigatorCategoryId: null,
            requireEventCreationRights: false,
            allow: {
                events: true,
                subcats: true
            }
        }, options);

        var $field = $('#' + options.fieldId);
        var $categoryTitle = $('#category-title-' + options.fieldId);
        var $dialogTrigger = $('#categorynav-button-' + options.fieldId);
        var hiddenData = $field.val() ? JSON.parse($field.val()) : {};
        var navigatorCategory = options.navigatorCategoryId;
        var actionOn = {};

        if (options.requireEventCreationRights) {
            actionOn.categoriesWithoutEventCreationRights = {disabled: true};
        }
        if (!options.allow.events) {
            actionOn.categoriesWithEvents = {disabled: true};
        }
        if (!options.allow.subcats) {
            actionOn.categoriesWithSubcategories = {disabled: true};
        }

        if (hiddenData) {
            $categoryTitle.text(hiddenData.title);
            $field.val(JSON.stringify(hiddenData));
        }

        $.ajax({
            url: build_url(Indico.Urls.Categories.info, {category_id: navigatorCategory}),
            dataType: 'json',
            error: handleAjaxError,
            success: function(data) {
                navigatorCategory = data;
            }
        });

        $dialogTrigger.on('click', function(evt) {
            evt.preventDefault();
            $('<div>').categorynavigator({
                category: navigatorCategory,
                openInDialog: true,
                actionOn: actionOn,
                onAction: function(category) {
                    var event = $.Event('indico:categorySelected');
                    var dfd = $.Deferred();
                    $categoryTitle.text(category.title);
                    hiddenData = {id: category.id, title: category.title};
                    navigatorCategory = category.id;
                    $field.val(JSON.stringify(hiddenData)).trigger('change').trigger(event, [category, dfd]);
                    if (event.isDefaultPrevented()) {
                        return dfd;
                    }
                }
            });
        });
    };
})(window);
