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

    function setupTableSorter() {
        $('#contribution-list .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    }

    function formatState(visible, total) {
        return $T.gettext('{0} / {1}').format('<strong>{0}</strong>'.format(visible.length),
                                              total.length);
    }

    function setState(visible, total) {
        var $state = $('#filtering-state'),
            title = '{0} out of {1} contributions displayed'.format(visible.length, total.length);
        $state.html(formatState(visible, total));

        // oldtitle needs to be updated too, because of qTip
        $state.attr({
            oldtitle: title,
            title: title
        });
    }

    function applyFilters() {
        var contributions = $('#contribution-list tbody tr'),
            term = $('#search-input').val().trim(),
            visibleEntries, m,
            $state = $('#filtering-state'),
            $filterPlaceholder = $('#filter-placeholder');

        $filterPlaceholder.hide();
        $state.removeClass('active');

        if (!term) {
            contributions.show();
            setState(contributions, contributions);
            return;
        }

        // quick search of contribution by ID
        if ((m = term.match(/^#(\d+)$/))) {
            visibleEntries = $('[data-friendly-id="' + m[1] + '"]');
        } else {
            visibleEntries = contributions.find('td[data-searchable*="' + term + '"]').closest('tr');
        }

        if (visibleEntries.length === 0) {
            $filterPlaceholder.text($T.gettext('There are no contributions that match your search criteria.')).show();
            $state.addClass('active');
        } else if (visibleEntries.length !== contributions.length) {
            $state.addClass('active');
        }

        setState(visibleEntries, contributions);

        contributions.hide();
        visibleEntries.show();

        // Needed because $(window).scroll() is not called when hiding elements
        // causing scrolling elements to be out of place.
        $(window).trigger('scroll');
    }

    function setupSearchBox() {
        $('#search-input').realtimefilter({
            callback: function() {
                applyFilters();
            }
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
                        startDateCol.html($('<em>', {'text': $T.gettext('Not scheduled')}));
                        showUndoWarning(
                            $T.gettext("'{0}' has been unscheduled due to the session change.").format(row.data('title')),
                            $T.gettext("Undo successful! Timetable entry and session have been restored."),
                            function() {
                                return patchObject(timetableRESTURL, 'POST', data.undo_unschedule).then(function(data) {
                                    startDateCol.text(moment(data.start_dt).format('DD/MM/YYYY HH:mm'));
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

    function setupFilterDialog() {
        $('#filter-button').ajaxDialog({
            title: $T.gettext('Contribution list configuration'),
            onClose: function(data) {
                if (data) {
                    $('#contribution-list').html(data.html);
                    $('#displayed-records-fragment').html(data.displayed_records_fragment);
                }
            }
        });
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

    global.setupContributionList = function setupContributionList(options) {
        options = $.extend({
            createSessionURL: null,
            createTrackURL: null,
            timetableRESTURL: null
        }, options);
        setupTableSorter();
        setupSearchBox();
        setupFilterDialog();
        setupStaticURLGeneration();
        setupSessionPicker(options.createSessionURL, options.timetableRESTURL);
        setupTrackPicker(options.createTrackURL);
        enableIfChecked('#contribution-list', 'input[name=contribution_id]', '.js-enable-if-checked');
        $('#contribution-list').on('indico:htmlUpdated', function() {
            setupTableSorter();
            applyFilters();
            setupSessionPicker(options.createSessionURL);
            setupTrackPicker(options.createTrackURL);
        });
    };
})(window);
