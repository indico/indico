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
        $('#contribution-list .session-item-picker').itempicker({
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
                                $('.session-item-picker').itempicker('updateItemList', data.sessions);
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
                        var startDateCol = row.find('td.start-date');
                        var oldLabelHtml = startDateCol.children().detach();

                        startDateCol.html($('<em>', {'text': $T.gettext('Not scheduled')}));
                        showUndoWarning(
                            $T.gettext("'{0}' has been unscheduled due to the session change.").format(row.data('title')),
                            $T.gettext("Undo successful! Timetable entry and session have been restored."),
                            function() {
                                return patchObject(timetableRESTURL, 'POST', data.undo_unschedule).then(function(data) {
                                    oldLabelHtml.filter('.label').text(moment.utc(data.start_dt).format('DD/MM/YYYY HH:mm'));
                                    startDateCol.html(oldLabelHtml);
                                    $this.itempicker('selectItem', oldSession ? oldSession.id : null);
                                });
                            }
                        );
                    }
                });
            }
        });
    }

    function setupTrackPicker(createURL) {
        $('#contribution-list .track-item-picker').itempicker({
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
                                $('.track-item-picker').itempicker('updateItemList', data.tracks);
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
    }

    function setupStartDateQBubbles() {
        $('.contrib-start-date').each(function() {
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
        $('.contrib-duration').each(function() {
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
            listItems: $('#contribution-list tbody tr'),
            term: $('#search-input'),
            state: $('#filtering-state'),
            placeholder: $('#filter-placeholder')
        };

        $('.report-section [data-toggle=dropdown]').closest('.group').dropdown();
        setupTableSorter('#contribution-list .tablesorter');
        setupSearchBox(filterConfig);
        setupSessionPicker(options.createSessionURL, options.timetableRESTURL);
        setupTrackPicker(options.createTrackURL);
        setupStartDateQBubbles();
        setupDurationQBubbles();
        enableIfChecked('#contribution-list', 'input[name=contribution_id]', '.js-enable-if-checked');
        $('#contribution-list').on('indico:htmlUpdated', function() {
            setupTableSorter('#contribution-list .tablesorter');
            applySearchFilters();
            setupSessionPicker(options.createSessionURL);
            setupTrackPicker(options.createTrackURL);
            setupStartDateQBubbles();
            setupDurationQBubbles();
        }).on('attachments:updated', function(evt) {
            var target = $(evt.target);
            reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
        });
        setupReporter();
        $('.js-submit-form').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            if (!$this.hasClass('disabled')) {
                $('#contribution-list form').attr('action', $this.data('href')).submit();
            }
        });
    };

    global.setupSubContributionList = function setupSubContributionList() {
        $('#subcontribution-list [data-toggle=dropdown]').closest('.group').dropdown();
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
    };
})(window);
