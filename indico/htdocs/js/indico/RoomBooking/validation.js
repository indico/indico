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

(function() {
    var validatingBooking = false;
    var validatingConflicts = false;
    var clickedButton = null;

    window.generateValidEndDates = function generateValidEndDates(startDate, endDate, frequency) {
        if (!(startDate instanceof Date) || !(endDate instanceof Date) ||
                [RRule.DAILY, RRule.WEEKLY, RRule.MONTHLY].indexOf(frequency) === -1) {
            return null;
        }

        var position = Math.ceil(startDate.getDate() / 7);
        if (position === 5) {
            // count 5th week as 'last' instead
            position = -1;
        }

        var rule_data = {
            freq: frequency,
            dtstart: startDate,
            until: endDate
        }

        // if monthly, preserve the week day/number
        if (frequency == RRule.MONTHLY) {
            _.extend(rule_data, {
                byweekday: RRule[startDate.getDayName().slice(0, 2).toUpperCase()],
                bysetpos:  position
            });
        }

        var rule = new RRule(rule_data);

        return _.map(rule.all(), function(dt) {
            if (dt <= startDate) { // the start date is not valid as an
                return null;       // end date for repetitive bookings.
            }
            return dt.setHours(0, 0, 0, 0);
        });

    };

    window.validateForm = function validateForm() {
        var isValid = true;

        if (!validatingBooking && !validatingConflicts) {
            return true;
        }

        // timerange
        if ($('#timerange').length) {
            isValid = isValid && $('#timerange').timerange('validate');
        }

        // repeatability
        if ($('#repeatability').length) {
            isValid = isValid && validate_repeatability();
        }

        // Booked for validator
        function validInput($element) {
            if ($element.attr('id') === 'room_usage') {
                return $('input[name=room_usage]:checked').val() !== undefined;
            } else if ($element.attr('id') === 'booked-for-user-wrapper') {
                if ($('input[name=room_usage]:checked').val() === 'other_user'){
                    return $('#booked_for_user').val() != '[]';
                }
                return true;
            } else {
                return !!$element.val().trim();
            }
        };

        $('#room_usage, #booked-for-user-wrapper, #booking_reason').each(function() {
            var $this = $(this);
            if (!validatingConflicts) {
                var valid = validInput($this);
                isValid = isValid && valid;
                $this.toggleClass('hasError', !valid);
            } else {
                $this.removeClass('hasError');
            }
        });

        // Collaboration validation
        if ($('#uses_vc').length) {
            var vcEnabled = $('#uses_vc').prop('checked');
            var vcErrors = vcEnabled != !!$('.js-vc-row input:not(#needs_vc_assistance):checked').length;
            var vcLabel = $('label[for="uses_vc"]');
            vcLabel.toggleClass('text-error', vcErrors);
            if (vcErrors) {
                vcLabel.attr('title', 'You need to select at least one piece of Videoconference equipment');
            }
            else {
                vcLabel.qtip('destroy', true).removeAttr('title');
            }
            isValid = isValid && !vcErrors;
        }
        return isValid;
    };

    function validate_repeatability() {
        var valid = true;
        var single_day = false;

        var repeat_frequency = $('input[name=repeat_frequency]:checked').val();
        var repeatability;
        var message;

        switch (repeat_frequency) {
            // Single Day
            case "0":
                single_day = true;
                break;
            // Repeat daily
            case "1":
                repeatability = RRule.DAILY;
                message = $T("Invalid end date for daily repetition");
                break;
            // Repeat weekly
            case "2":
                repeatability = RRule.WEEKLY;
                message = $T("Invalid end date for weekly repetition");
                break;
            // Repeat monthly
            case "3":
                repeatability = RRule.MONTHLY;
                message = $T("Invalid end date for monthly repetition");
                break;
            default:
                valid = false;
        }

        var start_date = $('#sDatePlace').datepicker('getDate');
        var end_date = $('#eDatePlace').datepicker('getDate');

        if (valid && !single_day) {
            valid = end_date > start_date;
            if (valid) {
                var validEndDates = window.generateValidEndDates(start_date, end_date, repeatability);
                valid = !!validEndDates.length && validEndDates.indexOf(end_date.getTime()) !== -1;
            }
        }

        var label = $('#repeatability .label');
        if (!valid) {
            if (typeof label.data('qtip') !== "object") {
                label.qtip({content: {text: message}});
            } else {
                label.qtip("api").set("content.text", message);
            }
            label.addClass('invalid');
            $('#edate').addClass('invalid');
        } else {
            label.removeClass('invalid');
            if (typeof label.data('qtip') === "object") {
                label.qtip("api").destroy();
            }
        }

        return valid;
    }

    function validate_conflict() {
        var canSubmit = _.every($('.js-confirm-warning'), function(e) {
            return e.checked;
        });

        var buttons = $('.js-submit-booking');
        var tooltip = $T('Please, confirm first you understood the implications of the conflicts mentioned above.');
        if ($('#bookingForm').data('onlyConflicts')) {
            tooltip = $T('Unable to book for the selected day(s).');
            canSubmit = false;
        }

        buttons.prop('disabled', !canSubmit);
        if (!canSubmit) {
            if (!buttons.parent().hasClass('qtip-disabled-wrapper')) {
                buttons.wrap($('<span>', {class: 'qtip-disabled-wrapper'}));
                buttons.after($('<span>', {class: 'qtip-disabled-holder', title: tooltip}));
            }
        } else {
            if (buttons.parent().hasClass('qtip-disabled-wrapper')) {
                buttons.siblings('.qtip-disabled-holder').remove();
                buttons.unwrap();
            }
        }

        return canSubmit;
    }

    $(function() {
        $('#searchForm').on('submit', function(e) {
            validatingBooking = true;
            if (!validateForm()) {
                e.preventDefault();
            } else if (!$("#roomselector").roomselector("validate")) {
                new AlertPopup($T("Error"), $T('Please select a room (or several rooms).')).open();
                e.preventDefault();
            } else {
                saveFormData();
            }
        });

        $('.js-submit-booking, #submit_check').on('click', function(e) {
            clickedButton = $(this).attr('name');
            if ($(this).data('validation') == 'check') {
                validatingConflicts = true;
                validatingBooking = false;
            } else {
                validatingConflicts = false;
                validatingBooking = true;
            }

            if (!validateForm()) {
                e.preventDefault();
                new AlertPopup($T("Error"), $T('Please fill in all the required fields (highlighted in red).')).open();
            }
        });

        $('#bookingForm :input').on('input change', function() {
            validateForm();
        });
        $('#bookingForm').on('submit', function(e) {
            if (validatingConflicts) {
                return;
            }
            e.preventDefault();
            var extraData = {};
            extraData[clickedButton] = '1';
            var killProgress = IndicoUI.Dialogs.Util.progress();
            $(this).ajaxSubmit({
                dataType: 'json',
                data: extraData,
                error: handleAjaxError,
                success: function(data) {
                    if (handleAjaxError(data)) {
                        return;
                    }
                    if (data.success) {
                        var userId = $('body').data('userId');
                        $.jStorage.set('rb-user-{0}'.format(userId), {});
                        location.href = data.url;
                    } else {
                        var error_box = $('.js-booking-creation-error-box').clone().show();
                        var errors = error_box.find('.js-booking-creation-error-message');
                        $.each(data.msg.split('\n'), function addError(_, error) {
                            errors.append($('<li>', {text: error}));
                        });
                        new AlertPopup($T("Booking creation error"), error_box[0]).open();
                    }
                },
                complete: function() {
                    killProgress();
                }
            });
        });

        $('.js-confirm-warning').on('change', function() {
            validate_conflict();
        });

        validate_conflict();
    });
})();
