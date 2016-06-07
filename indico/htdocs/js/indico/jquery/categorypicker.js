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
            self.categoryNavigator = $('<div>')
            .addClass('category-navigator i-box just-group-list with-hover-effect fixed-height')
            .append($('<div>').addClass('i-box-content'))
            .append(self.categoryList);

            buildCategoryList(opt.initialCateg, self.categoryList);

            self.element.append(self.searchInput).append(self.categoryNavigator);

            function goToCategory(categoryId, $categoryList) {
                $('.category-navigator .item').animate({
                    height: 0,
                    paddingTop: 0,
                    paddingBottom: 0,
                    border: 0
                }, {
                    complete: function() {
                        $(this).remove();
                    }
                });
                buildCategoryList(categoryId, $categoryList);
            }

            function buildCategoryList(categoryId, $categoryList) {
                $.ajax({
                    url: build_url(Indico.Urls.Categories.info, {categId: categoryId}),
                    dataType: 'json',
                    error: function(data) {
                        handleAjaxError(data);
                    },
                    success: function(data) {
                        if (data.category) {
                            var category = $('<li>', {
                                class: 'item parent-category',
                                data: {
                                    id: data.category.id
                                }
                            }).append($('<span>', {
                                class: 'title',
                                text: data.category.title,
                            }));
                            var breadcrumb = $('<ul>').addClass('breadcrumb');
                            _.each(data.category.breadcrumb, function(category) {
                                breadcrumb.append($('<li>')
                                    .append($('<a>', {
                                        text: category.title,
                                        data: {
                                            id: category.id
                                        },
                                        href: '#'
                                    }).on('click', function(evt) {
                                        evt.preventDefault()
                                        goToCategory($(this).data('id'), $categoryList);
                                    }))
                                );
                            });
                            category.append(breadcrumb);
                            $categoryList.append(category);
                        }
                        if (data.subcategories) {
                            _.each(data.subcategories, function(subcat) {
                                var subcategory = $('<li>', {
                                    class: 'item subcategory',
                                    data: {
                                        id: subcat.id
                                    }
                                }).append($('<span>', {
                                    class: 'title',
                                    text: subcat.title,
                                }));
                                subcategory.on('click', function() {
                                    goToCategory($(this).data('id'), $categoryList);
                                });
                                $categoryList.append(subcategory);
                            });
                        }
                    }
                });
            }
        }
    });
})(jQuery);
