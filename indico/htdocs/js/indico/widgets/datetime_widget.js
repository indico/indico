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

    global.setupDateTimeWidget = function setupDateTimeWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            timezoneFieldId: null,
            timezone: null,
            defaultTime: null,
            hasData: false,
            earliest: {
                date: null,
                time: null
            },
            latest: {
                date: null,
                time: null
            },
            linkedField: {
                id: null,
                notBefore: false,
                notAfter: false
            }
        }, options);

        var dateField = $('#' + options.fieldId + '-date');
        var timeField = $('#' + options.fieldId + '-time');
        var resetFieldAction = $('#' + options.fieldId + '-reset');
        var timezoneElement = timeField.next('.timezone');
        var timezone = options.timezone;
        var initialDate, initialTime;

        function clearDate() {
            dateField.datepicker('setDate', null).trigger('change');
        }

        function initTime() {
            if (timeField.val() === '') {
                timeField.val(options.defaultTime);
            }
        }

        function updateDateRequired(e) {
            dateField.prop('required', e.target.value !== '');
        }

        function updateTimeRequired(e) {
            timeField.prop('required', e.target.value !== '');
        }

        function updateResetFieldAction() {
            var isVisible = !!(dateField.val() || timeField.val());
            resetFieldAction.toggle(isVisible);
        }

        function updateTimeLimits(selectedDate, limitDate, limitTime, attr) {
            var selectedTime = timeField.val();
            if (selectedDate !== limitDate || (selectedDate === initialDate && selectedTime === initialTime)) {
                timeField.removeAttr(attr);
            } else if (timeField.attr(attr) !== limitTime) {
                // Fix for Chrome ignoring next number keydown after min/max attr change.
                // Delay gives some margin to type double digits.
                setTimeout(function() {
                    timeField.attr(attr, limitTime);
                }, 1000);
            }
        }

        function updateDateLimits(selectedDate) {
            if (options.linkedField.notBefore) {
                dateField.datepicker('option', 'minDate', selectedDate);
            }
            if (options.linkedField.notAfter) {
                dateField.datepicker('option', 'maxDate', selectedDate);
            }
        }

        function updateMaxTime(selectedDate) {
            updateTimeLimits(selectedDate, options.latest.date, options.latest.time, 'max');
        }

        function updateMinTime(selectedDate) {
            updateTimeLimits(selectedDate, options.earliest.date, options.earliest.time, 'min');
        }

        timezoneElement.qtip({
            content: {
                text: function() {
                    return timezone;
                }
            }
        });

        if (options.timezoneFieldId) {
            $('#' + options.timezoneFieldId).on('change', function() {
                timezone = $(this).val();
            });
        }

        dateField.datepicker({
            onSelect: function applyOnSelectHandlers() {
                var $this = $(this);
                var handlers = $this.data('onSelectHandlers');
                for (var i = 0; i < handlers.length; i++) {
                    handlers[i].apply(this, arguments);
                }
                // ensure we de-focus the field; otherwise clicking it again might
                // not re-open the datepicker
                $this.blur();
            }
        }).data('onSelectHandlers', [
            initTime,
            function() {
                dateField.trigger('change');
            }
        ]).on('change', function(e) {
            updateTimeRequired(e);
            updateResetFieldAction();
        }).on('keydown', function(e) {
            if (e.which === K.BACKSPACE) {
                e.preventDefault();
                clearDate();
            }
        });

        timeField.on('change', function applyOnChangeHandlers() {
            var handlers = $(this).data('onChangeHandlers');
            for (var i = 0; i < handlers.length; i++) {
                handlers[i].apply(this, arguments);
            }
        }).data('onChangeHandlers', [updateDateRequired, updateResetFieldAction]);

        if (options.hasData) {
            initialDate = dateField.val() || undefined;
            initialTime = timeField.val() || undefined;
            dateField.datepicker('setDate', initialDate);
            dateField.trigger('change');
            timeField.trigger('change');
        }

        if (options.earliest) {
            dateField.datepicker('option', 'minDate', options.earliest.date);
            dateField.datepicker().data('onSelectHandlers').push(updateMinTime);
            timeField.data('onChangeHandlers').push(function() {
                var selectedDate = moment(dateField.datepicker('getDate'));
                updateMinTime(selectedDate.format('DD/MM/YYYY'));
            });
            if (initialDate) {
                updateMinTime(initialDate);
            }
        }

        if (options.latest) {
            dateField.datepicker('option', 'maxDate', options.latest.date);
            dateField.datepicker().data('onSelectHandlers').push(updateMaxTime);
            timeField.data('onChangeHandlers').push(function() {
                var selectedDate = moment(dateField.datepicker('getDate'));
                updateMaxTime(selectedDate.format('DD/MM/YYYY'));
            });
            if (initialDate) {
                updateMaxTime(initialDate);
            }
        }

        if (options.linkedField) {
            var linkedDateField = $('#' + options.linkedField.id + '-date');
            linkedDateField.datepicker().data('onSelectHandlers').push(updateDateLimits);
            updateDateLimits(linkedDateField.datepicker('getDate'));
        }

        resetFieldAction.on('click', function resetDateTime() {
            timeField.val('').trigger('change');
            clearDate();
        });
    };
})(window);
