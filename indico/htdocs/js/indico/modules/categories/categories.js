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

(function(global) {
    'use strict';

    $(document).ready(function() {
        setupCategoryMoveButton();
    });

    function setupCategoryMoveButton() {
        $('.js-move-category').on('click', function(evt) {
            evt.preventDefault();
            $('<div>').categorynavigator({openInDialog: true});
        });
    }

    global.setupCategoryTable = function setupCategoryTable() {
        var $table = $('table.categories-management');
        var $tbody = $table.find('tbody');
        var $bulkDeleteButton = $('.js-bulk-delete-category');
        var categoryRowSelector = 'tr[data-category-id]';
        var checkboxSelector = 'input[name=category_id]';

        $('.js-sort-categories').on('click', function() {
            var currentOrder = getSortedCategories();
            function undo() {
                restoreCategoryOrder(currentOrder);
                return setOrderAjax(currentOrder);
            }
            sortCategories();
            setOrderAjax(getSortedCategories());
            cornerMessage({
                actionLabel: $T.gettext("Undo"),
                actionCallback: undo,
                feedbackMessage: $T.gettext("The category order has been restored."),
                duration: 10000,
                message: $T.gettext("The category list has been sorted.")
            });
        });

        $('.js-delete-category').on('indico:confirmed', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: 'POST',
                error: handleAjaxError,
                success: function(data) {
                    $this.closest(categoryRowSelector).remove();
                    if (data.is_empty) {
                        $('.banner .js-delete-category').removeClass('disabled')
                            .attr('title', $T.gettext("Delete category"));
                    }
                }
            });
        });

        enableIfChecked($tbody, checkboxSelector, $bulkDeleteButton, function($checkboxes) {
            return $checkboxes.filter(':not([data-is-empty=true])').length == 0;
        });
        $bulkDeleteButton.on('click', bulkDeleteCategories).qtip({
            suppress: false,
            content: {
                text: bulkDeleteButtonTooltipContent
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
                $tbody.find('[data-category-id=' + id + ']').detach().appendTo($tbody);
            });
        }

        function sortCategories() {
            $tbody.find(categoryRowSelector).sort(function(a, b) {
                return $(a).data('category-title').localeCompare($(b).data('category-title'));
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

        function updateCategoryDeleteButton() {
            if ($table.find(categoryRowSelector).length) {
                $('.banner .js-delete-category').addClass('disabled');
            } else {
                $('.banner .js-delete-category').removeClass('disabled')
                    .attr('title', $T.gettext("Delete category"));
            }
        }

        function bulkDeleteButtonTooltipContent() {
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
                        updateCategoryDeleteButton();
                    }
                }
            });
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
})(window);
