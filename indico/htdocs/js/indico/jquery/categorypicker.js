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

    $.widget('indico.categorypicker', {
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
            self._createNavigator();
            self._createSearchField();
            self.goToCategory(self.options.categoryId);
        },

        _createNavigator: function() {
            var self = this;
            self.$category = $('<div>');
            self.$categoryTree = $('<ul>', {class: 'group-list fixed-height'});
            self.$categoryResults = $('<ul>', {class: 'group-list fixed-height'});
            self.$categoryNavigator = $('<div>', {class: 'category-navigator i-box just-group-list with-hover-effect'})
                .append($('<div>', {class: 'i-box-content'})
                    .append(self.$category)
                    .append(self.$categoryTree)
                    .append(self.$categoryResults));
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
                filter: false,
                source: {
                    ajax: {
                        url: build_url(Indico.Urls.Categories.search),
                        path: 'categories',
                        data: {
                            q: "{{query}}"
                        }
                    }
                },
                resultContainer: false,
                cancelButton: false,
                display: 'title',
                callback: {
                    onClickAfter: function(node, a, item) {
                        self.goToCategory(item.id);
                    },
                    onResult: function(node, query, result) {
                        self._renderResults(result);
                    },
                    onHideLayout: function() {
                        self.$categoryResults.html('');
                        self.$category.show();
                        self.$categoryTree.show();
                    },
                    onShowLayout: function(node, query) {
                        self.$category.hide();
                        self.$categoryTree.hide();
                    }
                }
            });
        },

        _buildBreadcrumbs: function(path, clickable) {
            var self = this;
            var $breadcrumbs = $('<ul>', {class: 'breadcrumbs'});
            var tag = clickable ? '<a>' : '<span>';

            _.each(path, function(category) {
                var $item = $(tag, {text: category.title});
                if (clickable) {
                    $item.attr('href', '');
                    $item.attr('title', $T.gettext("Go to: {0}".format(category.title)));
                }
                self._bindGoToCategoryOnClick($item, category.id);
                $breadcrumbs.append($('<li>').append($item));
            });

            return $breadcrumbs;
        },

        _buildCategory: function(category, isSubcategory, withBreadcrumbs, clickableBreadcrumbs) {
            var self = this;
            var tag = isSubcategory ? '<li>' : '<div>';
            var itemClass = isSubcategory ? 'subcategory' : 'current-category';

            var $category = $(tag, {
                class: 'item ' + itemClass,
                id: 'category-' + category.id
            });

            var $categoryTitle = $('<div>', {class: 'title-wrapper'});
            $categoryTitle.append($('<span>', {
                class: 'title',
                text: category.title
            }));
            if (withBreadcrumbs) {
                $categoryTitle.append(self._buildBreadcrumbs(category.path, clickableBreadcrumbs));
            }

            $category.append($('<div>', {class: 'icon-wrapper'}));
            $category.append($categoryTitle);
            $category.append(self._buildSidePanel(category, !isSubcategory));
            return $category;
        },

        _buildCurrentCategory: function(category) {
            var self = this;
            return self._buildCategory(category, false, true, true);
        },

        _buildSubcategory: function(category, withBreadcrumbs) {
            var self = this;
            var $subcategory = self._buildCategory(category, true, withBreadcrumbs);

            if (category.can_access) {
                self._bindGoToCategoryOnClick($subcategory, category.id);
                $subcategory.addClass('can-access');
            }

            return $subcategory;
        },

        _buildSidePanel: function(category, withGoToParent) {
            var self = this;
            var $buttonWrapper = $('<div>', {class: 'button-wrapper'});

            $buttonWrapper.append($('<div>').append($('<span>', {
                class: 'action-button',
                text: self.options.actionButtonText
            }).on('click', function(evt) {
                evt.stopPropagation();
                self.options.onAction(category.id);
            })));

            if (withGoToParent && category.path && category.path.length) {
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

        _ellipsizeBreadcrumbs: function($category) {
            var self = this;
            var $breadcrumbs = $category.find('.breadcrumbs');
            var availableSpace = $category.find('.title-wrapper').width();
            var $ellipsis = $('<li>', {class: 'ellipsis'});
            var shortened = false;

            while ($breadcrumbs.outerWidth() >= availableSpace) {
                var $segments = $breadcrumbs.children(':not(.ellipsis)');
                var middleIndex = Math.floor($segments.length / 2);
                if (!shortened) {
                    $segments.eq(middleIndex).replaceWith($ellipsis);
                } else {
                    $segments.eq(middleIndex).remove();
                }
            }
        },

        _renderNavigator: function(data) {
            var self = this;

            if (data.category) {
                self.$category.html(self._buildCurrentCategory(data.category));
                self._ellipsizeBreadcrumbs(self.$category);
            }
            if (data.subcategories) {
                _.each(data.subcategories, function(subcategory) {
                    self.$categoryTree.append(self._buildSubcategory(subcategory));
                });
            }
        },

        _renderResults: function(categories) {
            var self = this;

            self.$categoryResults.html('');
            _.each(categories, function(category) {
                var $result = self._buildSubcategory(category, true);
                $result.find('.icon-wrapper').append($('<i>', {
                    class: 'icon-search',
                    title: $T.gettext("Search result")
                }));
                self.$categoryResults.append($result);
                self._ellipsizeBreadcrumbs($result);
            });
        },

        _bindGoToCategoryOnClick: function($element, id) {
            var self = this;

            $element.on('click', function(evt) {
                evt.preventDefault();
                self.goToCategory(id);
            });
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
                    url: build_url(Indico.Urls.Categories.info, {category_id: id}),
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
