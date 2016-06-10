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
    'use strict';

    $.widget("indico.categorypicker", {
        options: {
            categoryId: 0,
            actionButtonText: $T.gettext("Select"),
            onAction: function() {}
        },

        // Cache for data of already visited categories
        // Shared between instances
        _cache: {},

        _typeaheadTemplate:
        '<form>\
            <div class="typeahead__container">\
                <div class="typeahead__field">\
                    <span class="typeahead__query"></span>\
                </div>\
            </div>\
        </form>',

        _create: function() {
            var self = this;
            self._createSearchField();
            self._createNavigator();
            self.goToCategory(self.options.categoryId);
        },

        _createNavigator: function() {
            var self = this;
            self.$categoryList = $('<ul>', {class: 'group-list fixed-height'});
            self.$categoryNavigator = $('<div>', {class: 'category-navigator i-box just-group-list with-hover-effect'})
                .append($('<div>', {class: 'i-box-content'})
                    .append(self.$categoryList));
            self.element.append(self.$categoryNavigator);
        },

        _createSearchField: function() {
            var self = this;

            // Visible search field
            self.$searchInput = $('<input>', {
                class: 'js-search-category js-typeahead',
                type: 'search',
                name: 'q',
                placeholder: $T.gettext("Search")
            }).attr('autocomplete', 'off');

            // Insert elements in DOM
            var $typeaheadForm = $($.parseHTML(self._typeaheadTemplate)[0]);
            $typeaheadForm.find('.typeahead__query').append(self.$searchInput);
            self.element.prepend($typeaheadForm);

            // Typeahead init
            self.$searchInput.typeahead({
                dynamic: true,
                source: {
                    ajax: {
                        url: build_url(Indico.Urls.Categories.search),
                        path: 'categories',
                        data: {
                            q: "{{query}}"
                        }
                    }
                },
                cancelButton: false,
                display: 'title',
                callback: {
                    onClickAfter: function(node, a, item) {
                        self.goToCategory(item.id);
                    }
                }
            });
        },

        _buildBreadcrumbs: function(path) {
            var self = this;
            var $breadcrumbs = $('<ul>', {class: 'breadcrumbs'});

            _.each(path, function(category) {
                var $item = $('<a>', {
                    text: category.title,
                    'data-id': category.id,
                    title:  $T.gettext("Go to: {0}".format(category.title)),
                    href: '#'
                });
                self._bindClickEvent($item);
                $breadcrumbs.append($('<li>').append($item));
            });

            return $breadcrumbs;
        },

        _ellipsizeBreadcrumbs: function($breadcrumbs, availableSpace) {
            var self = this;
            var cutFromLeft = true;
            var items = $breadcrumbs.children();
            var middleIndex = Math.floor(items.length / 2);
            var leftList = items.slice(0, middleIndex);
            var rightList = items.slice(middleIndex, items.length);

            shortenBreadcrumbs(leftList, rightList);

            function shortenBreadcrumbs (leftList, rightList) {
                if ($breadcrumbs.width() >= availableSpace) {
                    if (cutFromLeft) {
                        leftList.splice(-1, 1);
                        cutFromLeft = false;
                    } else {
                        rightList.splice(0, 1);
                        cutFromLeft = true;
                    }
                    var newItemList = $.merge($.merge($.merge([], leftList), [$('<li>', {text: '...'}).get(0)]), rightList);
                    $breadcrumbs.empty();
                    _.each(newItemList, function(item) {
                        self._bindClickEvent($(item).find('a'));
                        $breadcrumbs.append(item);
                    });
                    shortenBreadcrumbs(leftList, rightList);
                }
            }
        },

        _buildCurrentCategory: function(category) {
            var self = this;

            var $category = $('<div>', {
                class: 'item current-category',
                'data-id': category.id,
                id: 'category-' + category.id
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
                'data-id': category.id,
                id: 'category-' + category.id
            }).append($('<span>', {
                class: 'title',
                text: category.title,
            })).append(self._buildSidePanel(category));

            if (category.can_access) {
                $subcategory.on('click', function() {
                    self.goToCategory($(this).data('id'));
                }).addClass('can-access');
            }

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
                var $currentCategory = self._buildCurrentCategory(data.category);
                self.$categoryList.before($currentCategory);
                var $breadcrumbs = $currentCategory.find('.breadcrumbs');
                var availableSpace = $currentCategory.width() - $currentCategory.find('.button-wrapper').width();
                if ($breadcrumbs.width() >= availableSpace) {
                    self._ellipsizeBreadcrumbs($breadcrumbs, availableSpace);
                }
            }
            if (data.subcategories) {
                _.each(data.subcategories, function(subcategory) {
                    self.$categoryList.append(self._buildSubcategory(subcategory));
                });
            }
        },

        _bindClickEvent: function($element) {
            var self = this;

            $element.on('click', function(evt) {
                evt.preventDefault();
                self.goToCategory($(this).data('id'));
            })
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

            if (self._cache[id]) {
                self._renderNavigator(self._cache[id]);
            } else {
                $.ajax({
                    url: build_url(Indico.Urls.Categories.info, {categId: id}),
                    dataType: 'json',
                    error: function(data) {
                        handleAjaxError(data);
                    },
                    success: function(data) {
                        if (data) {
                            self._cache[id] = data;
                            self._renderNavigator(data);
                        }
                    }
                });
            }
        }
    });
})(jQuery);
