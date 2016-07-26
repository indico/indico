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

    function colorizeFilter(filter) {
        filter.toggleClass('active', filter.find(':checked').length > 0);
    }

    function colorizeActiveFilters() {
        $('.report-filter .filter').each(function() {
            colorizeFilter($(this));
        });
    }

    global.setupReportFilter = function() {
        $('.report-filter').each(function() {
            $(this).find('.report-column').each(function() {
                var $reportColumn = $(this);
                $reportColumn.dropdown({selector: '.title', 'relative_to': $reportColumn});
            });
        });

        colorizeActiveFilters();

        $('.report-filter-dialog .js-reset-btn').on('click', function() {
            $('.report-filter input:checkbox:checked').prop('checked', false).trigger('change');
            $('.js-clear-filters-message').slideDown({
                done: function() {
                    $(this).delay(4000).slideUp();
                }
            });
        });

        $('.report-filter input:checkbox').on('change', function() {
            colorizeFilter($(this).closest('.filter'));
        });
    };

    function setupStaticURLGeneration() {
        $('.js-static-url').on('click', function() {
            var $this = $(this);
            $.ajax({
                method: 'POST',
                url: $this.data('href'),
                error: handleAjaxError,
                complete: IndicoUI.Dialogs.Util.progress(),
                success: function(data) {
                    $this.copyURLTooltip(data.url);
                }
            });
        });
    }

    global.setupReporter = function() {
        setupStaticURLGeneration();
        handleRowSelection();

        $('.report').on('indico:htmlUpdated', function() {
            handleRowSelection();
        });
    };
})(window);
