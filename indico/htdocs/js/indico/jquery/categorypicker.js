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
            categoryId: 0
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            self.$searchInput = $('<input>', {
                class: 'js-search-category',
                type: 'text',
                placeholder: $T.gettext("Search")
            });
            self.$categoryList = $('<ul>', {class: 'group-list'});
            self.$categoryNavigator = $('<div>', {class: 'category-navigator i-box just-group-list with-hover-effect fixed-height'})
                .append($('<div>', {class: 'i-box-content'})
                    .append(self.$categoryList));
            self.goToCategory(opt.categoryId);
            self.element.append(self.$searchInput).append(self.$categoryNavigator);
        },

        _buildBreadcrumbs: function(path) {
            var self = this;
            var $breadcrumbs = $('<ul>', {class: 'breadcrumbs'});

            _.each(path, function(category) {
                $breadcrumbs.append($('<li>')
                    .append($('<a>', {
                        text: category.title,
                        data: {id: category.id},
                        title:  $T.gettext("Go to: {0}".format(category.title)),
                        href: '#'
                    }).on('click', function(evt) {
                        evt.preventDefault()
                        self.goToCategory($(this).data('id'));
                    }))
                );
            });

            return $breadcrumbs;
        },

        _buildCurrentCategory: function(category) {
            var self = this;

            var $category = $('<div>', {
                class: 'item current-category',
                data: {id: category.id}
            });
            var $titleWrapper = $('<div>', {class: 'title-wrapper'})
            $titleWrapper.append($('<span>', {
                class: 'title',
                text: category.title,
            }));
            $titleWrapper.append(self._buildBreadcrumbs(category.path));
            $category.append($titleWrapper);
            if (category.path.length) {
                var parent = _.last(category.path);
                var $buttonWrapper = $('<div>', {class: 'button-wrapper'});
                $buttonWrapper.append($('<a>', {
                    class: 'icon-arrow-up navigate-up',
                    title: $T.gettext("Go to parent: {0}".format(parent.title))
                }).on('click', function() {
                    self.goToCategory(parent.id);
                }));
                $category.append($buttonWrapper);
            }

            return $category;
        },

        _buildSubcategory: function(subcategory) {
            var self = this;

            var $subcategory = $('<li>', {
                class: 'item subcategory',
                data: {id: subcategory.id}
            }).append($('<span>', {
                class: 'title',
                text: subcategory.title,
            })).on('click', function() {
                self.goToCategory($(this).data('id'));
            });

            return $subcategory;
        },

        _renderNavigator: function(data) {
            var self = this;

            if (data.category) {
                self.$categoryList.before(self._buildCurrentCategory(data.category));
            }
            if (data.subcategories) {
                _.each(data.subcategories, function(subcategory) {
                    self.$categoryList.append(self._buildSubcategory(subcategory));
                });
            }
        },

        goToCategory: function(id) {
            var self = this;

            $('.category-navigator .item').animate({
                height: 0,
                paddingTop: 0,
                paddingBottom: 0,
                border: 0
            }, {
                complete: function() {
                    $(this).remove();
                }
            }).find('.title').fadeOut();

            $.ajax({
                url: build_url(Indico.Urls.Categories.info, {categId: id}),
                dataType: 'json',
                error: function(data) {
                    handleAjaxError(data);
                },
                success: function(data) {
                    if (data) {
                        self._renderNavigator(data);
                    }
                }
            });
        }
    });
})(jQuery);
