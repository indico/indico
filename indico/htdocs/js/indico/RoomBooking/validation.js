/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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
        $('#contact_email, #booking_reason').each(function() {
            var $this = $(this);
            if (!validatingConflicts) {
                var valid = !!$this.val().trim();
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
                vcLabel.attr('title', 'You need to select at least one piece of Video Conference equipment');
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
                repeatability = 'days';
                message = $T("Period shorter than 1 day");
                break;
            // Repeat weekly
            case "2":
                repeatability = 'weeks';
                message = $T("Period shorter than 1 week");
                break;
            // Repeat monthly
            case "3":
                repeatability = 'months';
                message = $T("Period shorter than 1 month");
                break;
            default:
                valid = false;
        }

        if (valid && !single_day) {
            var start_date = moment($('#sDatePlace').datepicker('getDate'));
            var end_date = moment($('#eDatePlace').datepicker('getDate'));

            if (end_date.diff(start_date, repeatability) < 1) {
                valid = false;
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
                        error_box.find('.js-booking-creation-error-message').text(data.msg);
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
