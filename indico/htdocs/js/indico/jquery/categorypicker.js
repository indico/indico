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

(function($) {
    $.widget("indico.categorypicker", {

        options: {
            initialCateg: 0
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            self.searchInput = $('<input>', {
                class: 'js-search-category',
                type: 'text',
                placeholder: $T.gettext("Search")
            });
            self.categoryList = $('<ul>').addClass('group-list');
            self.categoryNavigator = $('<div>', {
                class: 'category-navigator i-box just-group-list with-hover-effect'
            })
            .append($('<div>').addClass('i-box-content'))
            .append(self.categoryList);

            this.buildCategoryList(self.element, opt.initialCateg, self.categoryList);

            self.element.append(self.searchInput).append(self.categoryNavigator);
        },

        buildCategoryList: function($element, categoryId, $categoryList) {
            $.ajax({
                url: $element.data('href'),
                method: 'POST',
                dataType: 'json',
                data: {categoryId: categoryId},
                error: function(data) {
                    handleAjaxError(data);
                },
                success: function(data) {
                    if (data.category) {
                        var category = $('<li>', {
                            text: data.category.title,
                            class: 'item parent-category',
                            data: {
                                id: data.category.id
                            }
                        });
                        $categoryList.append(category);
                    }
                    if (data.subcategories) {
                        for (var i = 0; i < data.subcategories.length; i++) {
                            var subcategory = $('<li>', {
                                text: data.subcategories[i].title,
                                class: 'item subcategory',
                                data: {
                                    id: data.subcategories[i].id
                                }
                            });
                            $categoryList.append(subcategory);
                        };
                    }
                }
            });
        }
    });
})(jQuery);
