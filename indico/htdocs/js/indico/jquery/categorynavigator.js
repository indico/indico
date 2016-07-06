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

    $.widget('indico.categorynavigator', {
        options: {
            // ID of the current category
            categoryId: 0,
            // The text contained in action buttons
            actionButtonText: $T.gettext("Select"),
            // A dialog opens with the navigator rendered on it
            openInDialog: false,
            // The title for the category navigator dialog
            dialogTitle: $T.gettext("Select a category"),
            // Disallow action on specific categories
            actionOn: {
                categoriesWithSubcategories: {
                    disabled: false,
                    message: $T.gettext("Not possible for categories containing subcategories")
                },
                categoriesWithEvents: {
                    disabled: false,
                    message: $T.gettext("Not possible for categories containing events")
                },
                categories: {
                    disabled: false,
                    message: $T.gettext("Not possible for this category"),
                    ids: []
                }
            },
            // Callback for action button
            // If it returns a deferred object the dialog will close only when it gets resolved
            onAction: function() {}
        },

        // Caches for data of already visited categories
        // Shared between instances
        _cache: {},
        _cacheSubcategories: {},

        // The search request that is awaiting for response
        _currentSearchRequest: null,

        _create: function() {
            var self = this;
            if (self.options.openInDialog) {
                self._createInDialog();
            } else {
                self._createInline();
            }
        },

        _createInline: function() {
            var self = this;
            self.element.addClass('categorynav');
            self._createList();
            self._createSearchField();
            self.goToCategory(self.options.categoryId);
        },

        _createInDialog: function() {
            var self = this;
            ajaxDialog({
                title: self.options.dialogTitle,
                content: $('<div>', {class: 'categorynav-dialog-content'}).append($('<div>'))[0].outerHTML,
                closeButton: true,
                fullyModal: true,
                onOpen: function(dialog) {
                    self.element = dialog.contentContainer.children().first();
                    self.dialog = dialog;
                    self._createInline();
                }
            });
        },

        _createList: function() {
            var self = this;
            self.$category = $('<div>');
            self.$categoryTree = $('<ul>', {class: 'group-list'});
            self.$categoryResultsList = $('<ul>', {class: 'group-list'});
            self.$categoryResultsInfo = $('<div>', {class: 'search-result-info'});
            self.$categoryResults = $('<div>', {class: 'search-results'})
                .append(self.$categoryResultsInfo)
                .append(self.$categoryResultsList);
            self.$categoryList = $('<div>', {class: 'category-list'})
                .append(self.$category)
                .append(self.$categoryTree)
                .append(self.$categoryResults);
            self.$categoryResults.hide();
            self.element.append(self.$categoryList);
        },

        _createSearchField: function() {
            var self = this;

            // Visible search field
            self.$searchInput = $('<input>', {
                class: 'js-search-category',
                type: 'search',
                name: 'q',
                placeholder: $T.gettext("Search")
            }).attr('autocomplete', 'off');
            self.element.prepend(self.$searchInput);

            self.$searchInput.on('input', _.debounce(function(evt) {
                var $this = $(this);
                var inputValue = $this.val().trim();

                if (!inputValue) {
                    self._clearSearch();
                }

                if (inputValue.length < 3) {
                    return;
                }

                self._currentSearchRequest = $.ajax({
                    url: build_url(Indico.Urls.Categories.search),
                    data: {q: inputValue},
                    beforeSend: function() {
                        if (self._currentSearchRequest != null) {
                            self._currentSearchRequest.abort();
                        }
                        self._toggleLoading(true);
                    },
                    complete: function() {
                        self._toggleLoading(false);
                    },
                    error: function(jqXHR) {
                        if (jqXHR.statusText === 'abort') {
                            return;
                        }
                        handleAjaxError(jqXHR);
                    },
                    success: function(data) {
                        if (self._isInDOM()) {
                            self.$category.hide();
                            self.$categoryTree.hide();
                            self._renderSearchResultInfo(data.categories.length, data.total_count);
                            self._renderSearchResults(data.categories);
                        }
                    }
                });
            }, 500));
        },

        _clearSearch: function() {
            var self = this;

            if (self._currentSearchRequest != null) {
                self._currentSearchRequest.abort();
            }
            self.$searchInput.val('');
            self.$categoryResults.hide();
            self.$categoryResultsList.empty();
            self.$categoryResultsInfo.empty();
            self.$category.show();
            self.$categoryTree.show();
        },

        _buildBreadcrumbs: function(path, clickable) {
            var self = this;
            var $breadcrumbs = $('<ul>', {class: 'breadcrumbs'});
            var tag = clickable ? '<a>' : '<span>';

            _.each(path, function(category, idx) {
                var $item = $('<li>');
                var $segment = $(tag, {text: category.title});
                if (idx == 0) {
                    $item.text($T.gettext("in "));
                }
                if (clickable) {
                    $segment.attr('href', '');
                    $segment.attr('title', $T.gettext("Go to: {0}".format(category.title)));
                }
                self._bindGoToCategoryOnClick($segment, category.id);
                $breadcrumbs.append($item.append($segment));
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

            var $protection = $('<div>', {class: 'protection-wrapper'});
            if (isSubcategory || category.is_protected) {
                $protection.append($('<span>', {class: 'protection'}).toggleClass('icon-shield', category.is_protected));
            }

            var $categoryTitle = $('<div>', {class: 'title-wrapper'});
            $categoryTitle.append($('<span>', {
                class: 'title',
                text: category.title
            }));
            if (withBreadcrumbs && category.parent_path.length) {
                $categoryTitle.append(self._buildBreadcrumbs(category.parent_path, clickableBreadcrumbs));
            }

            $category.append($('<div>', {class: 'icon-wrapper'}));
            $category.append($protection);
            $category.append($categoryTitle);
            $category.append(self._buildSidePanel(category, isSubcategory));
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

        _buildSidePanel: function(category, forSubcategory) {
            var self = this;
            var $buttonWrapper = $('<div>', {class: 'button-wrapper'});
            var categoriesWithSubcategories = self.options.actionOn.categoriesWithSubcategories;
            var categoriesWithEvents = self.options.actionOn.categoriesWithEvents;

            var $button = $('<span>', {
                class: 'action-button',
                text: self.options.actionButtonText
            });

            if (categoriesWithSubcategories.disabled && !categoriesWithEvents.disabled && category.deep_category_count) {
                $button.addClass('disabled').attr('title', categoriesWithSubcategories.message);
            }
            if (categoriesWithEvents.disabled && !categoriesWithSubcategories.disabled && category.has_events) {
                $button.addClass('disabled').attr('title', categoriesWithEvents.message);
            }
            if (self.options.actionOn.categories.disabled && _.contains(self.options.actionOn.categories.ids, category.id)) {
                $button.addClass('disabled').attr('title', self.options.actionOn.categories.message);
            }
            if (!$button.hasClass('disabled')) {
                $button.on('click', function(evt) {
                    evt.stopPropagation();
                    self._onAction(category);
                });
            } else {
                $button.on('click', function(evt) {
                    evt.stopPropagation();
                    evt.preventDefault();
                });
            }

            $buttonWrapper.append($('<div>').append($button));

            if (!forSubcategory && category.parent_path && category.parent_path.length) {
                var parent = _.last(category.parent_path);
                var $arrowUp = $('<a>', {
                    class: 'icon-arrow-up navigate-up',
                    title: $T.gettext("Go to parent: {0}".format(parent.title))
                }).on('click', function() {
                    self.goToCategory(parent.id);
                });
                $buttonWrapper.append($arrowUp);
            }

            if (forSubcategory) {
                var $info = $('<div>', {class: 'stats'})
                    .append($('<div>', {text: $T.ngettext("{0} category", "{0} categories", category.deep_category_count)
                                                .format(category.deep_category_count)}))
                    .append($('<div>', {text: $T.ngettext("{0} event", "{0} events", category.deep_event_count)
                                                .format(category.deep_event_count)}));
                $buttonWrapper.append($info);
            }

            return $buttonWrapper;
        },

        _ellipsizeBreadcrumbs: function($category) {
            var self = this;
            var $breadcrumbs = $category.find('.breadcrumbs');
            var availableSpace = $category.find('.title-wrapper').width();
            var $ellipsis = $('<li>', {class: 'ellipsis'});
            var shortened = false;

            // Prevent infinite loop if for any reason $category is not in DOM
            if (!availableSpace) {
                return;
            }

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

        _renderCurrentCategory: function(category) {
            var self = this;
            var $currentCategory = self._buildCurrentCategory(category);
            self.$category.replaceWith($currentCategory);
            self.$category = $currentCategory;
            self._ellipsizeBreadcrumbs(self.$category);
        },

        _renderCategoryTree: function(subcategories) {
            var self = this;
            _.each(subcategories, function(subcategory) {
                self.$categoryTree.append(self._buildSubcategory(subcategory));
            });
            self._postRenderList();
        },

        _renderSearchResults: function(categories) {
            var self = this;
            self.$categoryResultsList.empty();
            self.$categoryResults.show();
            _.each(categories, function(category) {
                var $result = self._buildSubcategory(category, true);
                if (category.is_favorite) {
                    $result.find('.icon-wrapper').append($('<i>', {
                        class: 'icon-star',
                        title: $T.gettext("In favourite categories")
                    }));
                } else {
                    $result.find('.icon-wrapper').append($('<i>', {
                        class: 'icon-search',
                        title: $T.gettext("Search result")
                    }));
                }
                self.$categoryResultsList.append($result);
                self._ellipsizeBreadcrumbs($result);
            });
            self._postRenderList();
        },

        _renderSearchResultInfo: function(count, totalCount) {
            var self = this;
            var $stats = $('<span>', {
                class: 'result-stats',
                text: totalCount ? $T.gettext("Displaying {0} out of {1} results. Make the search more specific for more accurate results.").format(count, totalCount)
                                 : $T.gettext("There are no results. Make the search more specific for more accurate results.")
            });
            var $clear = $('<a>', {
                class: 'clear',
                text: $T.gettext("Clear search")
            }).on('click', function() {
                self._clearSearch();
            });

            self.$categoryResultsInfo.empty();
            self.$categoryResultsInfo.append($stats).append($clear).show();
        },

        _postRenderList: function() {
            var self = this;
            var statsMaxWidth = 0;
            var $stats = self.$categoryList.find('.item:not(.hiding) .stats:visible');

            $stats.each(function() {
                var width = this.getBoundingClientRect().width;
                if (width > statsMaxWidth) {
                    statsMaxWidth = width;
                }
            });

            // Set uniform stats width for maintaining horizontal alignment
            $stats.width(Math.ceil(statsMaxWidth));

            // Make sure the list stays always scrolled at the top
            self.$categoryTree.scrollTop(0);
        },

        _bindGoToCategoryOnClick: function($element, id) {
            var self = this;

            $element.on('click', function(evt) {
                evt.preventDefault();
                self.goToCategory(id);
            });
        },

        _getCurrentCategory: function(id) {
            var self = this;
            var dfd = $.Deferred();

            function resolve() {
                dfd.resolve(self._cache[id]);
            }

            if (self._cache[id]) {
                _.defer(resolve);
            } else {
                self._fetchCategory(id, resolve);
            }

            return dfd.promise();
        },

        _getCategoryTree: function(id) {
            var self = this;
            var dfd = $.Deferred();

            function resolve() {
                var subcategories = [];
                _.each(self._cacheSubcategories[id], function(id) {
                    subcategories.push(self._cache[id]);
                });
                dfd.resolve(subcategories);
            }

            if (self._cacheSubcategories[id]) {
                _.defer(resolve);
            } else {
                self._fetchCategory(id, resolve);
            }

            return dfd.promise();
        },

        _fetchCategory: function(id, callback) {
            var self = this;
            $.ajax({
                url: build_url(Indico.Urls.Categories.info, {category_id: id}),
                dataType: 'json',
                beforeSend: function() {
                    self._toggleLoading(true, true);
                },
                complete: function() {
                    self._toggleLoading(false, true);
                },
                error: handleAjaxError,
                success: function(data) {
                    if (data && self._isInDOM()) {
                        self._fillCache(data);
                        callback();
                    }
                }
            });
        },

        _fillCache: function(data) {
            var self = this;
            self._cache[data.category.id] = _.omit(data.category, 'subcategories');
            self._cacheSubcategories[data.category.id] = _.pluck(data.subcategories, 'id');
            _.each(data.subcategories, function(subcategory) {
                self._cache[subcategory.id] = $.extend(self._cache[subcategory.id], subcategory);
            });
            _.each(data.supercategories, function(supercategory) {
                self._cache[supercategory.id] = $.extend(self._cache[supercategory.id], supercategory);
            });
        },

        _onAction: function(category) {
            var self = this;
            var res = self.options.onAction(category);

            if (res === undefined) {
                res = $.Deferred().resolve();
            }

            res.then(function() {
                if (self.dialog) {
                    self.dialog.close();
                }
            });
        },

        _toggleLoading: function(state, disableInput) {
            var self = this;
            self.$categoryList.toggleClass('loading', state);
            if (disableInput) {
                self.element.find('input').prop('disabled', self.$categoryList.hasClass('loading'));
            }
        },

        _isInDOM: function() {
            var self = this;
            return $.contains(document, self.element[0]);
        },

        goToCategory: function(id) {
            var self = this;

            self.$categoryList.find('.group-list .item').animate({
                height: 0,
                paddingTop: 0,
                paddingBottom: 0,
                border: 0
            }, {
                complete: function() {
                    $(this).remove();
                }
            }).addClass('hiding').find('.title').fadeOut();

            self._clearSearch();
            self._getCurrentCategory(id).then(self._renderCurrentCategory.bind(self));
            self._getCategoryTree(id).then(self._renderCategoryTree.bind(self));
        }
    });
})(jQuery);
