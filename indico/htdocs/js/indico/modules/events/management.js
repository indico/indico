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

    global.refreshPersonFilters = function refreshPersonFilters() {
        var personRows = $('#persons-list tr[data-person-roles]');
        var filters = $('#persons-list [data-filter]:checked').map(function() {
            return $(this).data('filter');
        }).get();

        var visibleEntries = personRows.filter(function() {
            var $this = $(this);

            return _.any(filters, function(filterName) {
                return $this.data('person-roles')[filterName];
            });
        });

        personRows.hide();
        visibleEntries.show();
        $('#persons-list').trigger('indico:syncEnableIfChecked');
    };

    global.setupEventPersonsList = function setupEventPersonsList() {
        enableIfChecked('#persons-list', '.select-row:visible', '#persons-list .js-requires-selected-row');
        $('#persons-list [data-toggle=dropdown]').closest('.group').dropdown();
        $('#persons-list [data-filter]').on('click', refreshPersonFilters);

        $('#persons-list td').on('mouseenter', function() {
            var $this = $(this);
            if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
                $this.attr('title', $this.text());
            }
        });

        $('#persons-list .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            headerTemplate: '',
            sortList: [[1, 0]]
        });

        $('#persons-list .js-count-label:not(.no-role)').qbubble({
            show: {
                event: 'mouseover'
            },
            hide: {
                fixed: true,
                delay: 100,
                event: 'mouseleave'
            },
            position: {
                my: 'left center',
                at: 'right center'
            },
            content: {
                text: function() {
                    var items = $(this).data('items');
                    var html = $('<ul class="qbubble-item-list">');

                    $.each(items, function() {
                        var item = $('<li>');
                        if (this.url) {
                            item.append($('<a>', {text: this.title, 'href': this.url}));
                        } else {
                            item.text(this.title);
                        }
                        html.append(item);
                    });

                    return html;
                }
            }
        });
        if ($('#person-list [data-no-account]').length > 0) {
            $('#no-account-dropdown').removeClass('disabled');
        }
        if ($('#person-list [data-no-account]').length === $('#person-list [data-already-invited]').length) {
            $('#not-invited-only').parent().hide();
        }
    };


    global.showUndoWarning = function showUndoWarning(message, feedbackMessage, actionCallback) {
        cornerMessage({
            message: message,
            progressMessage: $T.gettext("Undoing previous operation..."),
            feedbackMessage: feedbackMessage,
            actionLabel: $T.gettext('Undo'),
            actionCallback: actionCallback,
            duration: 10000,
            feedbackDuration: 4000,
            class: 'warning'
        });
    };


    global.handleRowSelection = function handleRowSelection() {
        $('table.i-table input.select-row').on('change', function() {
            $(this).closest('tr').toggleClass('selected', this.checked);
        }).trigger('change');
    };
})(window);
