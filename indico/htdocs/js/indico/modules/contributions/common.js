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

/* global showUndoWarning:false, setupListGenerator:false, setupSearchBox:false */
/* global reloadManagementAttachmentInfoColumn:false */

(function(global) {
    'use strict';

    function setupTableSorter(selector) {
        $(selector).tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            headerTemplate: '',
            sortList: [[1, 0]]
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

    function setupSessionPicker(createURL, timetableRESTURL) {
        $('#contribution-list').on('click', '.session-item-picker', function() {
            $(this).itempicker({
                filterPlaceholder: $T.gettext('Filter sessions'),
                containerClasses: 'session-item-container',
                footerElements: [{
                    title: $T.gettext('Assign new session'),
                    onClick: function(itemPicker) {
                        ajaxDialog({
                            title: $T.gettext('Add new session'),
                            url: createURL,
                            onClose: function(data) {
                                if (data) {
                                    $('.session-item-picker').each(function() {
                                        var $this = $(this);
                                        if ($this.data('indicoItempicker')) {
                                            $this.itempicker('updateItemList', data.sessions);
                                        } else {
                                            $this.data('items', data.sessions);
                                        }
                                    });
                                    itemPicker.itempicker('selectItem', data.new_session_id);
                                }
                            }
                        });
                    }
                }],
                onSelect: function(newSession, oldSession) {
                    var $this = $(this);
                    var styleObject = $this[0].style;
                    var postData =  {session_id: newSession ? newSession.id : null};

                    return patchObject($this.data('href'), $this.data('method'), postData).then(function(data) {
                        var label = newSession ? newSession.title : $T.gettext('No session');
                        $this.find('.label').text(label);

                        if (!newSession) {
                            styleObject.removeProperty('color');
                            styleObject.removeProperty('background');
                        } else {
                            styleObject.setProperty('color', '#' + newSession.colors.text, 'important');
                            styleObject.setProperty('background', '#' + newSession.colors.background, 'important');
                        }

                        if (data.unscheduled) {
                            var row = $this.closest('tr');
                            var startDateCol = row.find('td.start-date > .vertical-aligner');
                            var oldLabelHtml = startDateCol.children().detach();

                            startDateCol.html($('<em>', {text: $T.gettext('Not scheduled')}));
                            /* eslint-disable max-len */
                            showUndoWarning(
                                $T.gettext("'{0}' has been unscheduled due to the session change.").format(row.data('title')),
                                $T.gettext("Undo successful! Timetable entry and session have been restored."),
                                function() {
                                    return patchObject(timetableRESTURL, 'POST', data.undo_unschedule).then(function(data) {
                                        oldLabelHtml.filter('.label').text(' ' + moment.utc(data.start_dt).format('DD/MM/YYYY HH:mm'));
                                        startDateCol.html(oldLabelHtml);
                                        $this.itempicker('selectItem', oldSession ? oldSession.id : null);
                                    });
                                }
                            );
                        }
                    });
                }
            });
        });
    }

    function setupTrackPicker(createURL) {
        $('#contribution-list').on('click', '.track-item-picker', function() {
            $(this).itempicker({
                filterPlaceholder: $T.gettext('Filter tracks'),
                containerClasses: 'track-item-container',
                uncheckedItemIcon: '',
                footerElements: [{
                    title: $T.gettext('Add new track'),
                    onClick: function(trackItemPicker) {
                        ajaxDialog({
                            title: $T.gettext('Add new track'),
                            url: createURL,
                            onClose: function(data) {
                                if (data) {
                                    $('.track-item-picker').each(function() {
                                        var $this = $(this);
                                        if ($this.data('indicoItempicker')) {
                                            $this.itempicker('updateItemList', data.tracks);
                                        } else {
                                            $this.data('items', data.tracks);
                                        }
                                    });
                                    trackItemPicker.itempicker('selectItem', data.new_track_id);
                                }
                            }
                        });
                    }
                }],
                onSelect: function(newTrack) {
                    var $this = $(this);
                    var postData = {track_id: newTrack ? newTrack.id : null};

                    return patchObject($this.data('href'), $this.data('method'), postData).then(function() {
                        var label = newTrack ? newTrack.title : $T.gettext('No track');
                        $this.find('.label').text(label);
                    });
                }
            });
        });
    }

    function setupStartDateQBubbles() {
        $('.js-contrib-start-date').each(function() {
            var $this = $(this);

            $this.ajaxqbubble({
                url: $this.data('href'),
                qBubbleOptions: {
                    style: {
                        classes: 'qbubble-contrib-start-date'
                    }
                }
            });
        });
    }

    function setupDurationQBubbles() {
        $('.js-contrib-duration').each(function() {
            var $this = $(this);

            $this.ajaxqbubble({
                url: $this.data('href'),
                qBubbleOptions: {
                    style: {
                        classes: 'qbubble-contrib-duration'
                    }
                }
            });
        });
    }

    global.setupContributionList = function setupContributionList(options) {
        options = $.extend({
            createSessionURL: null,
            createTrackURL: null,
            timetableRESTURL: null
        }, options);

        var filterConfig = {
            itemHandle: 'tr',
            listItems: '#contribution-list tbody tr',
            term: '#search-input',
            state: '#filtering-state',
            placeholder: '#filter-placeholder'
        };

        $('.list-section [data-toggle=dropdown]').closest('.toolbar').dropdown();
        setupTableSorter('#contribution-list .tablesorter');
        setupSessionPicker(options.createSessionURL, options.timetableRESTURL);
        setupTrackPicker(options.createTrackURL);
        setupStartDateQBubbles();
        setupDurationQBubbles();
        enableIfChecked('#contribution-list', 'input[name=contribution_id]', '.js-enable-if-checked');

        var applySearchFilters = setupListGenerator(filterConfig);

        $('#contribution-list').on('indico:htmlUpdated', function() {
            setupTableSorter('#contribution-list .tablesorter');
            setupStartDateQBubbles();
            setupDurationQBubbles();
            _.defer(applySearchFilters);
        }).on('attachments:updated', function(evt) {
            var target = $(evt.target);
            reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
        });
        $('.js-submit-form').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            if (!$this.hasClass('disabled')) {
                $('#contribution-list form').attr('action', $this.data('href')).submit();
            }
        });
    };

    global.setupSubContributionList = function setupSubContributionList() {
        $('#subcontribution-list [data-toggle=dropdown]').closest('.toolbar').dropdown();
        setupTableSorter('#subcontribution-list .tablesorter');
        enableIfChecked('#subcontribution-list', 'input[name=subcontribution_id]', '#subcontribution-list .js-enable-if-checked');

        $('#subcontribution-list td.subcontribution-title').on('mouseenter', function() {
            var $this = $(this);
            if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
                $this.attr('title', $this.text());
            }
        });
        $('#subcontribution-list').on('attachments:updated', function(evt) {
            var target = $(evt.target);
            reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
        });


        $('#subcontribution-list table').sortable({
            items: '.js-sortable-subcontribution-row',
            handle: '.ui-sortable-handle',
            placeholder: 'sortable-placeholder',
            tolerance: 'pointer',
            distance: 10,
            axis: 'y',
            containment: '#subcontribution-list table',
            start: function(e, ui) {
                ui.placeholder.height(ui.helper.outerHeight());
            },
            update: function(e, ui) {
                var self = $(this);

                $.ajax({
                    url: ui.item.data('sort-url'),
                    method: 'POST',
                    data: {subcontrib_ids: self.sortable('toArray')},
                    error: handleAjaxError
                });
            }
        });
    };

    global.setupEventDisplayContributionList = function setupEventDisplayContributionList() {
        var filterConfig = {
            itemHandle: 'div.contribution-row',
            listItems: '#display-contribution-list div.contribution-row',
            term: '#search-input',
            state: '#filtering-state',
            placeholder: '#filter-placeholder'
        };

        var applySearchFilters = setupListGenerator(filterConfig);
        applySearchFilters();
    };

    global.setupEventDisplayAuthorList = function setupEventDisplayAuthorList() {
        var filterConfig = {
            itemHandle: '.author-list > li',
            listItems: '.author-list > li',
            term: '#search-input',
            state: '#filtering-state',
            placeholder: '#filter-placeholder'
        };

        var applySearchFilters = setupSearchBox(filterConfig);
        applySearchFilters();
    };
})(window);
