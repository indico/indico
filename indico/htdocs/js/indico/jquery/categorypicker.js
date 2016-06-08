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
            categoryId: 0,
            actionButtonText: $T.gettext("Select"),
            onAction: function() {}
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            self.cache = {};
            self.$searchInput = $('<input>', {
                class: 'js-search-category',
                type: 'text',
                placeholder: $T.gettext("Search")
            });
            self.$categoryList = $('<ul>', {class: 'group-list fixed-height'});
            self.$categoryNavigator = $('<div>', {class: 'category-navigator i-box just-group-list with-hover-effect'})
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
                        evt.preventDefault();
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
            var $titleWrapper = $('<div>', {class: 'title-wrapper'});
            $titleWrapper.append($('<span>', {
                class: 'title',
                text: category.title,
            }));
            $titleWrapper.append(self._buildBreadcrumbs(category.path));
            $category.append($titleWrapper);
            $category.append(self._buildSidePanel(category));

            return $category;
        },

        _buildSubcategory: function(category) {
            var self = this;

            var $subcategory = $('<li>', {
                class: 'item subcategory',
                data: {id: category.id}
            }).on('click', function() {
                self.goToCategory($(this).data('id'));
            }).append($('<span>', {
                class: 'title',
                text: category.title,
            })).append(self._buildSidePanel(category));

            return $subcategory;
        },

        _buildSidePanel: function(category) {
            var self = this;
            var $buttonWrapper = $('<div>', {class: 'button-wrapper'});


            $buttonWrapper.append($('<div>').append($('<span>', {
                class: 'action-button',
                text: self.options.actionButtonText
            }).on('click', function(evt) {
                evt.stopPropagation();
                self.options.onAction(category.id);
            })));

            if (category.path && category.path.length) {
                var parent = _.last(category.path);
                var $arrowUp = $('<a>', {
                    class: 'icon-arrow-up navigate-up',
                    title: $T.gettext("Go to parent: {0}".format(parent.title))
                }).on('click', function() {
                    self.goToCategory(parent.id);
                });
                $buttonWrapper.append($arrowUp);
            }

            if (category.is_protected) {
                var $protection = $('<div>').append($('<span>', {class: 'icon-shield'}));
                $buttonWrapper.append($protection);
            }

            var $info = $('<div>')
                .append($('<div>', {text: $T.ngettext("{0} category", "{0} categories", category.category_count)
                                            .format(category.category_count)}))
                .append($('<div>', {text: $T.ngettext("{0} event", "{0} events", category.event_count)
                                            .format(category.event_count)}));
            $buttonWrapper.append($info);

            return $buttonWrapper;
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

            if (self.cache[id]) {
                self._renderNavigator(self.cache[id]);
            } else {
                $.ajax({
                    url: build_url(Indico.Urls.Categories.info, {categId: id}),
                    dataType: 'json',
                    error: function(data) {
                        handleAjaxError(data);
                    },
                    success: function(data) {
                        if (data) {
                            self.cache[id] = data;
                            self._renderNavigator(data);
                        }
                    }
                });
            }
        }
    });
})(jQuery);
