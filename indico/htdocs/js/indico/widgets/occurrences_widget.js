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

    global.setupOccurrencesWidget = function setupOccurrencesWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            defaultTime: null,
            defaultDuration: null,
            timezone: null,
            timezoneFieldId: null
        }, options);

        var rowTemplate = $($.parseHTML($('#' + options.fieldId + '-template').html())).filter('.occurrence');
        var container = $('#' + options.fieldId + '-container');
        var dataField = $('#' + options.fieldId + '');
        var timezone = options.timezone;

        function createRow(data) {
            var row = rowTemplate.clone().insertBefore(container.find('.add-occurrence'));
            var prevRow = row.prev('.occurrence');
            if (!prevRow.length) {
                prevRow = null;
            }
            var prevOccurrence = prevRow && prevRow.data('occurrence') || null;
            var dateField = row.find('.datepicker');
            var timeField = row.find('.timepicker');
            var durationField = row.find('.durationpicker');

            row.find('.remove-occurrence').on('click', function() {
                removeRow(row);
            });

            row.find('.timezone').qtip({
                content: {
                    text: function() {
                        return timezone;
                    }
                }
            });

            dateField.datepicker({
                onSelect: function() {
                    var $this = $(this);
                    $this.trigger('change');
                    if (timeField.val() === '') {
                        timeField.val(options.defaultTime);
                    }
                    // ensure we de-focus the field; otherwise clicking it again might
                    // not re-open the datepicker
                    $this.blur();
                    updateData();
                }
            }).on('change', function(evt) {
                timeField.prop('required', !!evt.target.value);
            }).on('keydown', function(evt) {
                if (evt.which == K.BACKSPACE) {
                    evt.preventDefault();
                    dateField.datepicker('setDate', null);
                    updateData();
                } else if (evt.which == K.TAB) {
                    if (!evt.shiftKey) {
                        evt.preventDefault();
                        $(this).nextAll('.timepicker').focus();
                    }
                }
            });

            timeField.on('change', function(evt) {
                dateField.prop('required', !!evt.target.value);
                updateData();
            });

            durationField.on('change', function() {
                updateData();
            });

            if (data) {
                dateField.datepicker('setDate', moment(data.date).format('DD/MM/YYYY'));
                row.find('.timepicker').val(data.time);
                row.find('.durationpicker').val(data.duration);
                dateField.prop('required', true);
                timeField.prop('required', true);
            } else if (prevOccurrence) {
                dateField.datepicker('setDate', moment(prevOccurrence.date).add(1, 'day').format('DD/MM/YYYY'));
                row.find('.timepicker').val(prevOccurrence.time);
                row.find('.durationpicker').val(prevOccurrence.duration);
                dateField.prop('required', true);
                timeField.prop('required', true);
            } else {
                row.find('.durationpicker').val(options.defaultDuration);
            }

            updateRemoveButtons();
            updateData();
        }

        function createInitialRows() {
            JSON.parse(dataField.val()).forEach(function(data) {
                createRow(data);
            });
        }

        function removeRow(row) {
            row.remove();
            updateRemoveButtons();
            updateData();
        }

        function updateRemoveButtons() {
            var rows = container.find('.occurrence');
            rows.find('.remove-occurrence').toggle(rows.length > 1);
        }

        function updateData() {
            var data = container.find('.occurrence').map(function() {
                var $this = $(this);
                var date = moment($(this).find('.datepicker').datepicker('getDate'));
                var rv = {
                    date: date.isValid() ? date.format('YYYY-MM-DD') : '',
                    time: $(this).find('.timepicker').val(),
                    duration: +$(this).find('.durationpicker').val()
                };
                $this.data('occurrence', (!!rv.date && !!rv.time && !!rv.duration) ? rv : null);
                return rv;
            }).get();
            dataField.val(JSON.stringify(data)).trigger('change');
        }

        if (options.timezoneFieldId) {
            $('#' + options.timezoneFieldId).on('change', function() {
                timezone = $(this).val();
            });
        }

        container.find('.add-occurrence').on('click', function(evt) {
            evt.preventDefault();
            createRow();
        });

        createInitialRows();
    };
})(window);
