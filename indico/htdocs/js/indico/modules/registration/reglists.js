/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

    function getSelectedRows() {
        return $('.registrations input:checkbox:checked').map(function() {
            return $(this).val();
        }).get();
    }

    function handleRowSelection() {
        $('table.i-table input.select-row').on('change', function() {
            $(this).closest('tr').toggleClass('selected', this.checked);
            $('.js-requires-selected-row').toggleClass('disabled', !$('.registrations input:checkbox:checked').length);
        }).trigger('change');
    }

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

    function setupTableSorter() {
        $('.registrations .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            headerTemplate: '',
            headers: {
                0: {
                    sorter: false
                }
            }
        });
    }

    global.setupRegistrationList = function setupRegistrationList() {
        handleRowSelection();
        setupStaticURLGeneration();
        setupTableSorter();

        $('.registrations .toolbar')
        .dropdown()
        .on('click', '.js-dialog-action', function(e) {
            e.preventDefault();
            var $this = $(this);
            ajaxDialog({
                dialogClasses: 'reglist-filter-dialog',
                trigger: this,
                url: $this.data('href'),
                title: $this.data('title'),
                onClose: function(data) {
                    if (data) {
                        $('.registrations-table-wrapper').html(data.registration_list);
                        handleRowSelection();
                        setupTableSorter();
                    }
                }
            });
        });

        $('#select-all').on('click', function() {
            $('table.i-table input.select-row').prop('checked', true).trigger('change');
        });

        $('#select-none').on('click', function() {
            $('table.i-table input.select-row').prop('checked', false).trigger('change');
        });

        $('.js-dialog-send-email').ajaxDialog({
            getExtraData: function() {
                return {registration_id: getSelectedRows()};
            }
        });

        $('.js-submit-reglist-form').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            $('.registrations form').attr('action', $this.data('href')).submit();
        });

        $('.registrations').on('indico:confirmed', '.js-delete-registrations', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var selectedRows = getSelectedRows();
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: {registration_id: selectedRows},
                traditional: true,
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function() {
                    for (var i = 0; i < selectedRows.length; i++) {
                        var row = $('#registration-' + selectedRows[i]);
                        row.fadeOut('fast', function() {
                            $(this).remove();
                        });
                    }
                }
            });
        });

        $('.registrations').on('indico:confirmed', '.js-modify-status', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var selectedRows = getSelectedRows();
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: {
                    registration_id: selectedRows,
                    approve: $this.data('approve')
                },
                traditional: true,
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function(data) {
                    if (data) {
                        $('.registrations-table-wrapper').html(data.registration_list);
                        handleRowSelection();
                        setupTableSorter();
                    }
                }
            });
        });

        $('.registrations .toolbar').on('click', '.disabled', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });

        var principal = $('#indico-user-to-add').principalfield({
            onUpdate: function(users) {
                if (users.length) {
                    var url = $('.js-add-user').data('href');
                    location.href = build_url(url, {user: users[0].id});
                }
            }
        });

        $('.js-add-user').on('click', function() {
            principal.principalfield('choose');
        });
    };


    function colorizeFilter(filter) {
        filter.toggleClass('active', filter.find(':checked').length > 0);
    }

    function colorizeActiveFilters() {
        $('.reglist-filter .filter').each(function() {
            colorizeFilter($(this));
        });
    }

    global.setupRegistrationListFilter = function setupRegistrationListFilter() {
        $('.reglist-filter').dropdown({selector: '.reglist-column .title'});
        colorizeActiveFilters();

        var visibleColumnsRegItemsField = $('#visible-columns-reg-items');
        var regItemsData = JSON.parse(visibleColumnsRegItemsField.val());

        $('.reglist-column')
        .on('click', '.trigger', function() {
            var $this = $(this);
            var field = $this.closest('.reglist-column');
            var fieldId = field.data('id');
            var enabled = $this.hasClass('enabled');

            if (enabled) {
                regItemsData.splice(regItemsData.indexOf(fieldId), 1);
            } else {
                regItemsData.push(fieldId);
            }

            $this.toggleClass('enabled', !enabled);
            field.toggleClass('striped', enabled);
            visibleColumnsRegItemsField.val(JSON.stringify(regItemsData)).trigger('change');
        })
        .each(function() {
            var field = $(this);
            var fieldId = field.data('id');

            if (regItemsData.indexOf(fieldId) != -1) {
                field.find('.trigger').addClass('enabled');
            } else {
                field.addClass('striped');
            }
        });

        $('.js-reset-btn').on('click', function() {
            $('.reglist-filter input:checkbox').prop('checked', false).trigger('change');
        });

        $('.reglist-filter input:checkbox').on('change', function() {
            colorizeFilter($(this).closest('.filter'));
        });
    };
})(window);
