/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import 'indico/modules/events/util/types_dialog';

(function(global) {
    'use strict';

    function setupTableSorter() {
        $('#sessions .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            cssChildRow: 'session-blocks-row',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    }

    function setupPalettePickers() {
        $('.palette-picker-trigger').each(function() {
            var $this = $(this);
            $this.palettepicker({
                availableColors: $this.data('colors'),
                selectedColor: $this.data('color'),
                onSelect: function(background, text) {
                    $.ajax({
                        url: $(this).data('href'),
                        method: $(this).data('method'),
                        data: JSON.stringify({colors: {text: text, background: background}}),
                        dataType: 'json',
                        contentType: 'application/json',
                        error: handleAjaxError,
                        complete: IndicoUI.Dialogs.Util.progress()
                    });
                }
            });
        });
    }

    function patchObject(url, method, data) {
        return $.ajax({
            url: url,
            method: method,
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: 'application/json',
            error: handleAjaxError,
            complete: IndicoUI.Dialogs.Util.progress()
        });
    }

    var filterConfig = {
        itemHandle: 'tr',
        listItems: '#sessions-wrapper tr.session-row',
        term: '#search-input',
        state: '#filtering-state',
        placeholder: '#filter-placeholder'
    };

    global.setupSessionsList = function setupSessionsList(options) {
        options = $.extend({
            createTypeURL: null
        }, options);
        setupTypePicker(options.createTypeURL);
        enableIfChecked('#sessions-wrapper', '.select-row', '#sessions .js-requires-selected-row');
        setupTableSorter();
        setupPalettePickers();
        handleRowSelection(false);
        var applySearchFilters = setupSearchBox(filterConfig);

        $('#sessions .toolbar').on('click', '.disabled', function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
        });

        $('#sessions-wrapper').on('indico:htmlUpdated', function() {
            setupTableSorter();
            setupPalettePickers();
            handleRowSelection(true);
            _.defer(applySearchFilters);
        }).on('click', '.show-session-blocks', function() {
            var $this = $(this);
            ajaxDialog({
                title: $this.data('title'),
                url: $this.data('href')
            });
        }).on('attachments:updated', function(evt) {
            var target = $(evt.target);
            reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
        });

        $('.js-submit-session-form').on('click', function(evt) {
            evt.preventDefault();
            var $this = $(this);

            if (!$this.hasClass('disabled')) {
                $('#sessions-wrapper form').attr('action', $this.data('href')).submit();
            }
        });
    };

    function setupTypePicker(createURL) {
        $('#sessions').on('click', '.session-type-picker', function() {
            $(this).itempicker({
                filterPlaceholder: $T.gettext('Filter types'),
                containerClasses: 'session-type-container',
                uncheckedItemIcon: '',
                footerElements: [{
                    title: $T.gettext('Add new type'),
                    onClick: function(sessionTypePicker) {
                        ajaxDialog({
                            title: $T.gettext('Add new type'),
                            url: createURL,
                            onClose: function(data) {
                                if (data) {
                                    $('.session-type-picker').each(function() {
                                        var $this = $(this);
                                        if ($this.data('indicoItempicker')) {
                                            $this.itempicker('updateItemList', data.types);
                                        } else {
                                            $this.data('items', data.types);
                                        }
                                    });
                                    sessionTypePicker.itempicker('selectItem', data.new_type_id);
                                }
                            }
                        });
                    }
                }],
                onSelect: function(newType) {
                    var $this = $(this);
                    var postData = {type_id: newType ? newType.id : null};

                    return patchObject($this.data('href'), $this.data('method'), postData).then(function() {
                        var label = newType ? newType.title : $T.gettext('No type');
                        $this.find('.label').text(label);
                    });
                }
            });
        });
    }
})(window);
