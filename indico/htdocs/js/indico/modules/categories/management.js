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

    // Category cache
    var _categories = {};

    global.setupCategoryMoveButton = function setupCategoryMoveButton(parentCategoryId) {
        if (parentCategoryId) {
            _fetchSourceCategory(parentCategoryId);
        }
        $('.js-move-category').on('click', function(evt) {
            var $this = $(this);
            _moveCategories([$this.data('categoryId')], _categories[parentCategoryId], $this.data('href'));
        });
    };

    global.setupCategoryTable = function setupCategoryTable(categoryId) {
        _fetchSourceCategory(categoryId);
        var $table = $('table.category-management');
        var $tbody = $table.find('tbody');
        var $bulkDeleteButton = $('.js-bulk-delete-category');
        var $bulkMoveButton = $('.js-bulk-move-category');
        var categoryRowSelector = 'tr[data-category-id]';
        var checkboxSelector = 'input[name=category_id]';


        $('.js-sort-categories').on('click', function() {
            var sortOrder = $(this).data('sort-order');
            var currentOrder = getSortedCategories();
            function undo() {
                restoreCategoryOrder(currentOrder);
                return setOrderAjax(currentOrder);
            }
            sortCategories(sortOrder);
            setOrderAjax(getSortedCategories());
            cornerMessage({
                actionLabel: $T.gettext("Undo"),
                actionCallback: undo,
                feedbackMessage: $T.gettext("The category order has been restored."),
                duration: 10000,
                message: $T.gettext("The category list has been sorted.")
            });
        });

        $bulkMoveButton.on('click', function(evt) {
            var $this = $(this);
            evt.preventDefault();
            if ($this.hasClass('disabled')) {
                return;
            }
            _moveCategories(getSelectedCategories(), _categories[categoryId], $this.data('href'));
        });

        $table.find('.js-move-category').on('click', function(evt) {
            var $this = $(this);
            _moveCategories([$this.data('categoryId')], _categories[categoryId], $this.data('href'));
        });

        $table.find('.js-delete-category').on('indico:confirmed', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: 'POST',
                error: handleAjaxError,
                success: function(data) {
                    $this.closest(categoryRowSelector).remove();
                    updateCategoryDeleteButton(data.is_parent_empty);
                }
            });
        });

        enableIfChecked($tbody, checkboxSelector, $bulkDeleteButton, function($checkboxes) {
            return $checkboxes.filter(':not([data-is-empty=true])').length == 0;
        });
        $bulkDeleteButton.on('click', bulkDeleteCategories).qtip({
            suppress: false,
            content: {
                text: getBulkDeleteButtonTooltipContent
            }
        });

        enableIfChecked($tbody, checkboxSelector, $bulkMoveButton);
        $bulkMoveButton.qtip({
            suppress: false,
            content: {
                text: getBulkMoveButtonTooltipContent
            }
        });

        $tbody.sortable({
            axis: 'y',
            containment: 'parent',
            cursor: 'move',
            handle: '.js-handle',
            items: '> tr',
            tolerance: 'pointer',
            update: function() {
                setOrderAjax(getSortedCategories());
            }
        });

        function getSortedCategories() {
            return $tbody.find(categoryRowSelector).map(function() {
                return $(this).data('category-id');
            }).toArray();
        }

        function restoreCategoryOrder(order) {
            $.each(order, function(index, id) {
                $tbody.find('[data-category-id=' + id + ']').not('.js-move-category').detach().appendTo($tbody);
            });
        }

        function sortCategories(sortOrder) {
            $tbody.find(categoryRowSelector).sort(function(a, b) {
                return sortOrder * strnatcmp($(a).data('category-title'), $(b).data('category-title'));
            }).detach().appendTo($tbody);
        }

        function setOrderAjax(order) {
            return $.ajax({
                url: $table.data('sort-url'),
                method: 'POST',
                data: JSON.stringify({
                    categories: order
                }),
                dataType: 'json',
                contentType: 'application/json',
                error: handleAjaxError
            });
        }

        function updateCategoryDeleteButton(enabled) {
            if (enabled) {
                $('.banner .js-delete-category').removeClass('disabled')
                    .attr('title', $T.gettext("Delete category"));
            } else {
                $('.banner .js-delete-category').addClass('disabled')
                    .attr('title', $T.gettext("This category cannot be deleted because it is not empty."));
            }
        }

        function getBulkDeleteButtonTooltipContent() {
            var $checked = getSelectedRows();
            if ($checked.length) {
                if ($bulkDeleteButton.hasClass('disabled')) {
                    return $T.gettext("At least one selected category cannot be deleted because it is not empty.");
                } else {
                    return $T.ngettext("Delete the selected category", "Delete {0} selected categories",
                                       $checked.length).format($checked.length);
                }
            } else {
                return $T.gettext("Select the categories to delete first.");
            }
        }

        function bulkDeleteCategories() {
            var $selectedRows = getSelectedRows();
            ajaxDialog({
                url: $table.data('bulk-delete-url'),
                method: 'POST',
                title: $T.gettext("Delete categories"),
                data: {
                    category_id: getSelectedCategories()
                },
                onClose: function(data) {
                    if (data && data.success) {
                        // Prevent other categories from being selected when someone reloads
                        // the page after deleting a selected category.
                        $selectedRows.find('input[type=checkbox]').prop('checked', false);
                        $selectedRows.remove();
                        updateCategoryDeleteButton(data.is_empty);
                    }
                }
            });
        }

        function getBulkMoveButtonTooltipContent() {
            var $checked = getSelectedRows();
            if ($checked.length) {
                return $T.ngettext("Move the selected category", "Move the {0} selected categories", $checked.length)
                    .format($checked.length);
            } else {
                return $T.gettext("Select the categories to move first.");
            }
        }

        function getSelectedCategories() {
            return $table.find(categoryRowSelector).find(checkboxSelector + ':checked').map(function() {
                return this.value;
            }).toArray();
        }

        function getSelectedRows() {
            return $table.find(categoryRowSelector).has(checkboxSelector + ':checked');
        }
    };

    global.setupCategoryEventList = function setupCategoryEventList(categoryId) {
        _fetchSourceCategory(categoryId);
        enableIfChecked('#event-management', 'input[name=event_id]', '.js-enabled-if-checked');

        $('.event-management .js-move-event-to-subcategory').on('click', function(evt) {
            evt.preventDefault();
            _moveEvents(_categories[categoryId], $(this).data('href'));
        });

        $('.js-event-management-toolbar .js-move-events-to-subcategory').on('click', function(evt) {
            evt.preventDefault();

            if ($(this).hasClass('disabled')) {
                return;
            }

            var data = {};
            if (isEverythingSelected()) {
                data.all_selected = 1;  // do NOT change this to true - the code on the server expects '1'
            } else {
                data.event_id = _.map($('#event-management input[name=event_id]:checkbox:checked'), function(obj) {
                    return obj.value;
                });
            }

            _moveEvents(_categories[categoryId], $(this).data('href'), data);
        });

        var isEverythingSelected = paginatedSelectAll({
            containerSelector: '#event-management',
            checkboxSelector: 'input:checkbox[name=event_id]',
            allSelectedSelector: 'input:checkbox[name=all_selected]',
            selectionMessageSelector: '#selection-message',
            totalRows: $('#event-management').data('total'),
            messages: {
                allSelected: function(total) {
                    return $T.ngettext('*', 'All {0} events in this category are currently selected.').format(total);
                },
                pageSelected: function(selected, total) {
                    return $T.ngettext('Only {0} out of {1} events is currently selected.',
                                       'Only {0} out of {1} events are currently selected.',
                                       selected).format(selected, total);
                }
            }
        }).isEverythingSelected;
    };

    function _fetchSourceCategory(categoryId) {
        if (_categories[categoryId] === undefined) {
            _categories[categoryId] = categoryId;
            $.ajax({
                url: build_url(Indico.Urls.Categories.info, {category_id: categoryId}),
                dataType: 'json',
                error: function(xhr) {
                    // XXX: Re-enable error handling once we skip retrieving protected parents
                    if (xhr.status !== 403) {
                        handleAjaxError(xhr);
                    }
                },
                success: function(data) {
                    _categories[categoryId] = data;
                }
            });
        }
    }

    function _moveCategories(ids, source, endpoint) {
        var sourceId = _.isObject(source) ? source.category.id : source;
        var data = {category_id: ids};

        $('<div>').categorynavigator({
            category: source,
            confirmation: true,
            openInDialog: true,
            actionButtonText: $T.gettext("Move here"),
            dialogTitle: $T.ngettext("Move category", "Move categories", ids.length),
            dialogSubtitle: $T.ngettext("Select new category parent for the category",
                                        "Select new category parent for {0} selected categories",
                                        ids.length).format(ids.length),
            actionOn: {
                categoriesWithEvents: {disabled: true},
                categoriesDescendingFrom: {
                    disabled: true,
                    ids: ids
                },
                categories: {
                    disabled: true,
                    groups: [{
                        ids: [sourceId],
                        message: $T.ngettext("The category is already here",
                                             "The selected categories are already here",
                                             ids.length)
                    }, {
                        ids: ids,
                        message: $T.ngettext("This is the category you are trying to move",
                                             "This is one of the categories you are trying to move",
                                             ids.length)
                    }]
                }
            },
            onAction: function(category) {
                $.ajax({
                    url: endpoint,
                    type: 'POST',
                    data: $.extend({'target_category_id': category.id}, data),
                    error: handleAjaxError,
                    success: function(data) {
                        if (data.success) {
                            location.reload();
                        }
                    }
                });
            }
        });
    }

    function _moveEvents(source, endpoint, data) {
        var sourceId = _.isObject(source) ? source.category.id : source;
        var eventCount = data ? (data.all_selected ? $('#event-management').data('total') : data.event_id.length) : 1;

        $('<div>').categorynavigator({
            category: source,
            confirmation: true,
            openInDialog: true,
            actionButtonText: $T.gettext("Move here"),
            dialogTitle: $T.ngettext("Move event", "Move events", eventCount),
            dialogSubtitle: $T.ngettext("Select category destination for the event",
                                        "Select category destination for {0} selected events".format(eventCount),
                                        eventCount),
            actionOn: {
                categoriesWithSubcategories: {
                    disabled: true
                },
                categoriesWithoutEventCreationRights: {
                    disabled: true
                },
                categories: {
                    disabled: true,
                    ids: [sourceId],
                    message: $T.ngettext("The event is already here",
                                         "The selected events are already here",
                                         eventCount)
                }
            },
            onAction: function(category) {
                $.ajax({
                    url: endpoint,
                    type: 'POST',
                    data: $.extend({'target_category_id': category.id}, data || {}),
                    error: handleAjaxError,
                    success: function(data) {
                        if (data.success) {
                            location.reload();
                        }
                    }
                });
            }
        });
    }
})(window);
