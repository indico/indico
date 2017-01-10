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

/* global Palette:false */
/* eslint-disable max-len */

(function($) {
    'use strict';

    $.widget('indico.categorynavigator', {
        options: {
            // ID or serialized data of the current category
            category: 0,
            // Text for action buttons
            actionButtonText: $T.gettext("Select"),
            // Prompt confirmation before action
            confirmation: false,
            // Text for placeholder in empty categories
            emptyCategoryText: $T.gettext("This category doesn't contain any subcategory"),
            // A dialog opens with the navigator rendered on it
            openInDialog: false,
            // The title for the category navigator dialog
            dialogTitle: $T.gettext("Select a category"),
            // The subtitle for the category navigator dialog
            dialogSubtitle: null,
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
                categoriesWithoutEventCreationRights: {
                    disabled: false,
                    message: $T.gettext("Not possible for categories where you cannot create events")
                },
                categoriesDescendingFrom: {
                    disabled: false,
                    ids: [],
                    // The closest parent category title will be used if more than one parent is present in ids
                    message: $T.gettext('Not possible for categories descending from category "{0}"')
                },
                categories: {
                    disabled: false,
                    message: $T.gettext("Not possible for this category"),
                    ids: [],
                    // Expects an Array of {ids: [...], message: '...'} for more specific messages
                    groups: []
                }
            },
            // Callback for action button
            // If it returns a deferred object the dialog will close only when it gets resolved
            onAction: function() {}
        },

        // Caches for data of already visited categories and search results
        // Shared between instances
        _categories: {},
        _subcategories: {},
        _searchResultData: {},

        // Requests awaiting for response
        _currentCategoryRequest: null,
        _currentSearchRequest: null,

        _create: function() {
            var self = this;
            if (_.isObject(self.options.category)) {
                self._fillCache(self.options.category);
                self._categoryId = self.options.category.category.id;
            } else {
                self._categoryId = self.options.category;
            }
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
            self._createBindings();
            self.goToCategory(self._categoryId);
        },

        _createInDialog: function() {
            var self = this;
            var $content = $('<div>', {class: 'categorynav-dialog-content'});
            ajaxDialog({
                title: self.options.dialogTitle,
                subtitle: self.options.dialogSubtitle,
                content: $content[0].outerHTML,
                closeButton: true,
                fullyModal: true,
                onOpen: function(dialog) {
                    self.element = dialog.contentContainer.children('.categorynav-dialog-content');
                    self.dialog = dialog;
                    self._createInline();
                }
            });
        },

        _createList: function() {
            var self = this;
            self.$category = $('<div>');
            self.$categoryTree = $('<ul>', {class: 'group-list'});
            self.$categoryResultsList = $('<ul>', {class: 'group-list search-results-list'});
            self.$categoryResultsInfo = $('<div>', {class: 'search-result-info'});
            self.$spinner = $('<div>', {class: 'spinner-wrapper'})
                .append($('<div>', {class: 'i-spinner'}));
            self.$placeholderEmpty = $('<div>', {class: 'placeholder'});
            self.$placeholderNoResults = $('<div>', {class: 'placeholder'});
            self.$categoryList = $('<div>', {class: 'category-list'})
                .append(self.$category)
                .append(self.$categoryTree)
                .append(self.$categoryResultsInfo)
                .append(self.$categoryResultsList)
                .append(self.$spinner)
                .append(self.$placeholderEmpty)
                .append(self.$placeholderNoResults);
            self._toggleSearchResultsView(false);
            self.element.append(self.$categoryList);
        },

        _createSearchField: function() {
            var self = this;
            self.$searchInput = $('<input>', {
                type: 'search',
                placeholder: $T.gettext("Search")
            });
            self.element.prepend(self.$searchInput);
            self.$searchInput.realtimefilter({
                wait: 500,
                callback: function(value) {
                    if (!value) {
                        self._clearSearch();
                    } else {
                        self.searchCategories(value);
                    }
                }
            });
        },

        _createBindings: function() {
            var self = this;
            self.element.on('click', '.js-action', function(evt) {
                var $this = $(this);
                evt.stopPropagation();
                if (!$this.hasClass('disabled')) {
                    self._onAction($this.data('categoryId'));
                }
            });
            self.element.on('click', '.js-go-to', function(evt) {
                var categoryId = $(this).data('categoryId');
                self.goToCategory(categoryId);
                evt.preventDefault();
            });
            self.element.on('click', '.js-navigate-up', function() {
                var parentId = $(this).data('parentId');
                self.goToCategory(parentId);
            });
            self.element.on('click', '.js-search', function() {
                self.$searchInput.focus();
                self.$searchInput.effect('highlight', {color: Palette.highlight});
            });
            self.element.on('click', '.js-clear-search', function() {
                self._clearSearch();
            });
        },

        _buildBreadcrumbs: function(path, clickable) {
            var $breadcrumbs = $('<ul>', {class: 'breadcrumbs'});
            var tag = clickable ? '<a>' : '<span>';

            _.each(path, function(category, idx) {
                var $item = $('<li>');
                var $segment = $(tag, {
                    'text': category.title,
                    'data-category-id': category.id
                }).toggleClass('js-go-to', clickable);
                if (idx === 0) {
                    $item.text($T.gettext("in") + " ");
                }
                if (clickable) {
                    $segment.attr('href', '');
                    $segment.attr('title', $T.gettext("Go to: {0}".format(category.title)));
                }
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

            var $categoryTitle = $('<div>', {class: 'title-wrapper'});
            $categoryTitle.append($('<span>', {
                class: 'title',
                text: category.title
            }));

            if (withBreadcrumbs && category.parent_path.length) {
                var $breadcrumbs = self._buildBreadcrumbs(category.parent_path, clickableBreadcrumbs);
                $categoryTitle.append($breadcrumbs);
            }

            $category.append($('<div>', {class: 'icon-wrapper'}));
            $category.append($categoryTitle);
            $category.append(self._buildSidePanel(category, isSubcategory));

            var $protectionIcon = $('<span>', {
                class: 'protection',
                title: $T.gettext("This category is protected")
            }).toggleClass('icon-shield', category.is_protected);
            if (isSubcategory) {
                var $protection = $('<div>', {class: 'protection-wrapper'}).append($protectionIcon);
                $categoryTitle.before($protection);
            } else if (category.is_protected) {
                $breadcrumbs.before($protectionIcon);
            }

            return $category;
        },

        _buildCurrentCategory: function(category) {
            var self = this;
            return self._buildCategory(category, false, true, true);
        },

        _buildSubcategory: function(category, withBreadcrumbs) {
            var self = this;
            var $subcategory = self._buildCategory(category, true, withBreadcrumbs, false);

            if (category.can_access) {
                $subcategory.addClass('can-access js-go-to');
                $subcategory.data('categoryId', category.id);
            }

            return $subcategory;
        },

        _buildSidePanel: function(category, forSubcategory) {
            var self = this;
            var $buttonWrapper = $('<div>', {class: 'button-wrapper'});
            var $button = $('<span>', {
                'class': 'action-button js-action',
                'text': self.options.actionButtonText,
                'data-category-id': category.id
            });
            $buttonWrapper.append($('<div>').append($button));

            var canActOn = self._canActOn(category, true);
            if (!canActOn.allowed) {
                $button.addClass('disabled').attr('title', canActOn.message);
            }

            if (!forSubcategory && category.parent_path && category.parent_path.length) {
                var parent = _.last(category.parent_path);
                var $arrowUp = $('<a>', {
                    'class': 'icon-arrow-up navigate-up js-navigate-up',
                    'title': $T.gettext("Go to parent: {0}".format(parent.title)),
                    'data-parent-id': parent.id
                });
                $buttonWrapper.append($arrowUp);
            }

            if (forSubcategory) {
                var $info = $('<div>', {
                    class: 'stats icon-list',
                    title: $T.ngettext("{0} category", "{0} categories", category.deep_category_count)
                             .format(category.deep_category_count) + ' | ' +
                           $T.ngettext("{0} event", "{0} events", category.deep_event_count)
                             .format(category.deep_event_count)
                });
                var $categories = $('<span>', {
                    class: 'categories-count',
                    text: category.deep_category_count
                });
                var $events = $('<span>', {
                    class: 'events-count',
                    text: category.deep_event_count
                });
                var $separator = $('<span>', {
                    class: 'stats-separator',
                    text: ' | '
                });
                $info.append($categories).append($separator).append($events);
                $buttonWrapper.append($info);
            }

            return $buttonWrapper;
        },

        _buildPlaceholder: function(category) {
            var self = this;
            var $placeholder = $('<div>')
                .append($('<div>', {class: 'placeholder-text', text: self.options.emptyCategoryText}));
            var parent = _.last(category.parent_path);
            var actionButtonText = self.options.actionButtonText.toLowerCase();
            var html;
            if (!category.parent_path.length) {
                // Root category is empty
                if (self._canActOn(category)) {
                    html = $T.gettext('You can only <a class="js-action" data-category-id="{0}">{1}</a> this one.')
                             .format(category.id, actionButtonText);
                }
            } else if (self._canActOn(category)) {
                html = $T.gettext('You can <a class="js-action" data-category-id="{0}">{1}</a> this one, ' +
                                  '<a class="js-navigate-up" data-parent-id="{2}">navigate up</a> ' +
                                  'or <a class="js-search">search</a>.')
                         .format(category.id, actionButtonText, parent.id);
            } else {
                html = $T.gettext('You can <a class="js-navigate-up" data-parent-id="{2}">navigate up</a> ' +
                                  'or <a class="js-search">search</a>.')
                         .format(category.id, actionButtonText, parent.id);
            }
            $placeholder.append($('<div>', {html: html}));
            return $placeholder;
        },

        _buildNoResultsPlaceholder: function() {
            var $placeholder = $('<div>')
                .append($('<div>', {
                    class: 'placeholder-text',
                    text: $T.gettext("Your search doesn't match any category")
                }))
                .append($('<div>', {
                    html: $T.gettext('You can <a class="js-search">modify</a> or ' +
                                     '<a class="js-clear-search">clear</a> your search.')
                }));
            return $placeholder;
        },

        _ellipsizeBreadcrumbs: function($category) {
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

        _highlightQuery: function(query, $result) {
            var $title = $result.find('.title');
            var title = $title.text();
            var indexStart = title.toLowerCase().search(query.toLowerCase());
            var indexEnd = indexStart + query.length;

            $title.html(title.substring(0, indexStart) + '<strong>' + title.substring(indexStart, indexEnd) +
                        '</strong>' + title.substring(indexEnd));
        },

        _renderCurrentCategory: function(category) {
            var self = this;
            var $currentCategory = self._buildCurrentCategory(category);
            self.$category.replaceWith($currentCategory);
            self.$category = $currentCategory;
            self._ellipsizeBreadcrumbs(self.$category);
        },

        _renderCategoryTree: function(subcategories, category) {
            var self = this;
            _.each(subcategories, function(subcategory) {
                self.$categoryTree.append(self._buildSubcategory(subcategory));
            });
            if (!subcategories.length) {
                self.$placeholderEmpty.html(self._buildPlaceholder(category));
            }
            self._postRenderList();
        },

        _renderSearchResults: function(categories, query) {
            var self = this;
            self.$category.hide();
            self.$categoryResultsList.empty();
            self._toggleSearchResultsView(true);
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
                self._highlightQuery(query, $result);
                self.$categoryResultsList.append($result);
                self._ellipsizeBreadcrumbs($result);
            });
            if (!categories.length) {
                self.$placeholderNoResults.html(self._buildNoResultsPlaceholder());
            } else {
                self.$placeholderNoResults.empty();
            }
            self._postRenderList();
        },

        _renderSearchResultInfo: function(count, totalCount) {
            var self = this;
            var $stats = $('<span>', {
                class: 'result-stats',
                text: totalCount ? $T.gettext("Displaying {0} out of {1} results.").format(count, totalCount)
                                 : $T.gettext("There are no results.")
            });
            if (totalCount !== count || !totalCount) {
                $stats.text($stats.text() + ' ' + $T("Make the search more specific for more accurate results"));
            }
            var $clear = $('<a>', {
                class: 'clear js-clear-search',
                text: $T.gettext("Clear search")
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

            // Indents subcategories when protection icon is visible
            var hasProtectedCategories = !!self.$categoryTree.find('.icon-shield').length;
            self.$categoryTree.toggleClass('with-protected', hasProtectedCategories);

            // Make sure the list stays always scrolled at the top
            self.$categoryTree.scrollTop(0);
        },

        _getCurrentCategory: function(id) {
            var self = this;
            var dfd = $.Deferred();

            function resolve() {
                dfd.resolve(self._categories[id]);
            }

            if (self._categories[id]) {
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
                _.each(self._subcategories[id], function(scId) {
                    subcategories.push(self._categories[scId]);
                });
                dfd.resolve(subcategories, self._categories[id]);
            }

            if (self._subcategories[id]) {
                _.defer(resolve);
            } else {
                self._fetchCategory(id, resolve);
            }

            return dfd.promise();
        },

        _getSearchResults: function(query) {
            var self = this;
            var dfd = $.Deferred();

            function resolve() {
                dfd.resolve(self._searchResultData[query], query);
            }

            if (self._searchResultData[query]) {
                _.defer(resolve);
            } else {
                self._fetchSearchResults(query, resolve);
            }

            return dfd.promise();
        },

        _fetchCategory: function(id, callback) {
            var self = this;

            // Don't send another request if one for the same ID is ongoing
            if (self._currentCategoryRequest && self._currentCategoryRequest.categoryId === id) {
                self._currentCategoryRequest.then(callback);
                return;
            }

            self._currentCategoryRequest = $.ajax({
                url: build_url(Indico.Urls.Categories.info, {category_id: id}),
                dataType: 'json',
                beforeSend: function() {
                    self._toggleLoading(true, true);
                },
                complete: function() {
                    self._toggleLoading(false, true);
                    self._currentCategoryRequest = null;
                },
                error: function(xhr) {
                    // XXX: Re-enable error handling once we skip retrieving protected parents
                    if (xhr.status !== 403) {
                        handleAjaxError(xhr);
                    }
                },
                success: function(data) {
                    if (data && self._isInDOM()) {
                        self._fillCache(data);
                        callback();
                    }
                }
            });

            self._currentCategoryRequest.categoryId = id;
        },

        _fetchReachableCategories: function(id) {
            var self = this;
            $.ajax({
                url: build_url(Indico.Urls.Categories.infoFrom, {category_id: id}),
                method: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    exclude: _.map(_.keys(self._subcategories), function(n) {
                        return +n;
                    })
                }),
                success: function(data) {
                    if (data) {
                        _.each(data.categories, function(category) {
                            self._fillCache(category);
                        });
                    }
                }
            });
        },

        _fetchSearchResults: function(query, callback) {
            var self = this;

            function fillCache(data) {
                self._searchResultData[query] = data;
                _.each(data.categories, self._fillSingleCategoryCache.bind(self));
            }

            self._currentSearchRequest = $.ajax({
                url: build_url(Indico.Urls.Categories.search),
                data: {q: query},
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
                    if (data && self._isInDOM()) {
                        fillCache(data);
                        callback();
                    }
                }
            });
        },

        _fillCache: function(data) {
            var self = this;
            self._categories[data.category.id] = _.omit(data.category, 'subcategories');
            self._subcategories[data.category.id] = _.pluck(data.subcategories, 'id');
            _.each(data.subcategories, self._fillSingleCategoryCache.bind(self));
            _.each(data.supercategories, self._fillSingleCategoryCache.bind(self));
        },

        _fillSingleCategoryCache: function(category) {
            var self = this;
            self._categories[category.id] = $.extend(self._categories[category.id], category);
        },

        _clearSearch: function() {
            var self = this;

            if (self._currentSearchRequest != null) {
                self._currentSearchRequest.abort();
            }
            self.$category.show();
            self.$searchInput.realtimefilter('clear');
            self._toggleSearchResultsView(false);
            self.$placeholderNoResults.empty();
            self._toggleTreeView(true);
        },

        _onAction: function(categoryId) {
            var self = this;

            function callback() {
                var res = self.options.onAction(self._categories[categoryId]);
                if (res === undefined) {
                    res = $.Deferred().resolve();
                }

                res.then(function() {
                    if (self.dialog) {
                        self.dialog.close();
                    }
                });
            }

            if (self.options.confirmation) {
                var text = $T.gettext("You selected category <em>{0}</em>. Are you sure you want to proceed?")
                             .format(self._categories[categoryId].title);
                confirmPrompt(text, $T.gettext("Confirm action")).then(callback);
            } else {
                callback();
            }
        },

        _canActOn: function(category, withMessage) {
            var self = this;
            var result = {allowed: true, message: ""};
            var canActOnCategories = self._canActOnCategories(category, true);
            var canActOnCategoriesDescendingFrom = self._canActOnCategoriesDescendingFrom(category, true);
            var canActOnCategoriesWithEvents = self._canActOnCategoriesWithEvents(category, true);
            var canActOnCategoriesWithSubcategories = self._canActOnCategoriesWithSubcategories(category, true);
            var canActOnCategoriesWithoutEventCreationRights = self._canActOnCategoriesWithoutEventCreationRights(category, true);

            if (!canActOnCategories.allowed) {
                result = canActOnCategories;
            } else if (!canActOnCategoriesDescendingFrom.allowed) {
                result = canActOnCategoriesDescendingFrom;
            } else if (!canActOnCategoriesWithEvents.allowed) {
                result = canActOnCategoriesWithEvents;
            } else if (!canActOnCategoriesWithSubcategories.allowed) {
                result = canActOnCategoriesWithSubcategories;
            } else if (!canActOnCategoriesWithoutEventCreationRights.allowed) {
                result = canActOnCategoriesWithoutEventCreationRights;
            }

            return withMessage ? result : result.allowed;
        },

        _canActOnCategoriesWithoutEventCreationRights: function(category, withMessage) {
            var self = this;
            var result = {allowed: true, message: ""};
            var categoriesWithoutEventCreationRights = self.options.actionOn.categoriesWithoutEventCreationRights;
            if (categoriesWithoutEventCreationRights.disabled && !category.can_create_events) {
                result.allowed = false;
                result.message = categoriesWithoutEventCreationRights.message;
            }
            return withMessage ? result : result.allowed;
        },

        _canActOnCategoriesWithSubcategories: function(category, withMessage) {
            var self = this;
            var result = {allowed: true, message: ""};
            var hasSubcategories = !!category.deep_category_count;
            var categoriesWithSubcategories = self.options.actionOn.categoriesWithSubcategories;
            if (categoriesWithSubcategories.disabled && hasSubcategories) {
                result.allowed = false;
                result.message = categoriesWithSubcategories.message;
            }
            return withMessage ? result : result.allowed;
        },

        _canActOnCategoriesWithEvents: function(category, withMessage) {
            var self = this;
            var result = {allowed: true, message: ""};
            var hasOnlyEvents = category.has_events && !category.deep_category_count;
            var categoriesWithEvents = self.options.actionOn.categoriesWithEvents;
            if (categoriesWithEvents.disabled && hasOnlyEvents) {
                result.allowed = false;
                result.message = categoriesWithEvents.message;
            }
            return withMessage ? result : result.allowed;
        },

        _canActOnCategoriesDescendingFrom: function(category, withMessage) {
            var self = this;
            var result = {allowed: true, message: ""};
            var categoriesDescendingFrom = self.options.actionOn.categoriesDescendingFrom;

            if (categoriesDescendingFrom.disabled) {
                var id;
                var pathIds = _.pluck(category.parent_path, 'id').reverse();
                var ids = categoriesDescendingFrom.ids;
                for (var i in pathIds) {
                    id = pathIds[i];
                    if (_.contains(ids, id)) {
                        result.allowed = false;
                        result.message = categoriesDescendingFrom.message.format(self._categories[id].title);
                        break;
                    }
                }
            }

            return withMessage ? result : result.allowed;
        },

        _canActOnCategories: function(category, withMessage) {
            var self = this;
            var result = {allowed: true, message: ""};
            var categories = self.options.actionOn.categories;

            if (categories.disabled) {
                if (_.contains(categories.ids, category.id)) {
                    result.allowed = false;
                    result.message = categories.message;
                } else {
                    for (var i in categories.groups) {
                        var group = categories.groups[i];
                        if (_.contains(group.ids, category.id)) {
                            result.allowed = false;
                            result.message = group.message;
                            break;
                        }
                    }
                }
            }

            return withMessage ? result : result.allowed;
        },

        _toggleLoading: function(state, disableInput) {
            var self = this;
            self.$categoryList.toggleClass('loading', state);
            if (disableInput) {
                self.element.find('input').prop('disabled', state);
            }
        },

        _toggleTreeView: function(visible) {
            var self = this;
            self.$category.toggle(visible);
            self.$categoryTree.toggle(visible);
            self.$placeholderEmpty.toggleClass('hidden', !visible);
        },

        _toggleSearchResultsView: function(visible) {
            var self = this;
            self.$categoryResultsInfo.toggle(visible);
            self.$categoryResultsList.toggle(visible);
        },

        _isInDOM: function() {
            var self = this;
            return $.contains(document, self.element[0]);
        },

        goToCategory: function(id) {
            var self = this;

            function render() {
                self._clearSearch();
                self.$categoryTree.empty();
                self._getCurrentCategory(id).then(self._renderCurrentCategory.bind(self));
                self._getCategoryTree(id).then(self._renderCategoryTree.bind(self));
                self._fetchReachableCategories(id);
            }

            self.$placeholderEmpty.empty();
            if (!self.$categoryTree.is(':empty')) {
                self.$categoryTree.slideUp(300, render);
            } else {
                render();
            }
        },

        searchCategories: function(query) {
            var self = this;

            if (query.length < 3) {
                return;
            }

            self._toggleTreeView(false);
            self._toggleSearchResultsView(false);
            self._getSearchResults(query).then(function(data, query) {  // eslint-disable-line no-shadow
                self._renderSearchResultInfo(data.categories.length, data.total_count);
                self._renderSearchResults(data.categories, query);
            });
        }
    });
})(jQuery);
