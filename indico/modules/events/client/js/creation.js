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

/* eslint-disable import/unambiguous */
(function(global) {
    global.setupEventCreationDialog = function setupEventCreationDialog(options) {
        options = $.extend({
            categoryField: null,
            protectionModeFields: null,
            initialCategory: null,
            checkAvailability: false,
            rbExcludedCategories: null,
            serverDefaultTimezone: null
        }, options);

        const messages = $($.parseHTML($('#event-creation-protection-messages').html()));
        const protectionMessage = $('<div>', {class: 'form-group', css: {marginTop: '5px'}});

        const $createBooking = $('#event-creation-create_booking');
        const $availableMessage = $('#room-available');
        const $availablePrebookMessage = $('#room-available-prebook');
        const $conflictBookingMessage = $('#room-conflict-booking');
        const $conflictPrebookingMessage = $('#room-conflict-prebooking');
        const $conflictPrebookingPrebookMessage = $('#room-conflict-prebooking-prebook');
        const $userBookingMessage = $('#room-user-booking');
        const $userPrebookingMessage = $('#room-user-prebooking');
        const $unbookableMessage = $('#room-unbookable');
        const $cantBookMessage = $('#room-cant-book');

        let currentCategory = null;
        let previousRoomId, $currentMessage, startDt, endDt, category, roomData, timezone;

        protectionMessage.appendTo(options.protectionModeFields.closest('.form-field'));

        function updateProtectionMessage() {
            let mode = options.protectionModeFields.filter(':checked').val();
            if (mode === 'inheriting') {
                mode = currentCategory.is_protected ? 'inheriting-protected' : 'inheriting-public';
            }
            const elem = messages.filter('.{0}-protection-message'.format(mode));
            elem.find('.js-category-title').text(currentCategory.title);
            protectionMessage.html(elem);
        }

        options.categoryField.on('indico:categorySelected', (evt, cat) => {
            if (!currentCategory) {
                options.protectionModeFields.prop('disabled', false);
                options.protectionModeFields.filter('[value=inheriting]').prop('checked', true);
            }
            currentCategory = cat;
            updateProtectionMessage();
        });

        options.protectionModeFields.on('change', function() {
            updateProtectionMessage();
        });

        if (options.initialCategory) {
            options.categoryField.trigger('indico:categorySelected', [options.initialCategory]);
        } else {
            options.protectionModeFields.prop('disabled', true);
        }

        function setLectureTimes(occurrence) {
            startDt = moment(`${occurrence['date']} ${occurrence['time']}`, 'DD-MM-YYYY HH:mm');
            endDt = moment(startDt).add(occurrence['duration'], 'minutes');
        }

        function initAvailabilityValues() {
            const startDate = $('#event-creation-start_dt-date').val();
            const startTime = $('#event-creation-start_dt-time').val();
            const endDate = $('#event-creation-end_dt-date').val();
            const endTime = $('#event-creation-end_dt-time').val();
            const occurrencesVal = $('#event-creation-occurrences').val();
            const occurrences = occurrencesVal ? JSON.parse(occurrencesVal) : null;

            roomData = JSON.parse($('#event-creation-location_data').val());
            timezone = $('#event-creation-timezone').val();
            category = JSON.parse($('#event-creation-category').val());

            if (occurrences && occurrences.length === 1) {
                setLectureTimes(occurrences[0]);
            } else {
                startDt = moment(`${startDate} ${startTime}`, 'DD/MM/YYYY HH:mm');
                endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
            }
        }

        function isCategoryExcluded(categoryId) {
            options.rbExcludedCategories.some((excludedCategory) => {
                return (parseInt(excludedCategory.id, 10) === categoryId);
            });
        }

        function hideAvailability() {
            if ($currentMessage) {
                $currentMessage.hide();
            }
        }

        function updateAvailability() {
            hideAvailability();

            if (!('room_id' in roomData) ||
                !startDt.isSame(endDt, 'day') ||
                isCategoryExcluded(category['id']) ||
                timezone !== options.serverDefaultTimezone) {
                $createBooking.val(false);
                return;
            }

            const roomId = roomData['room_id'];
            previousRoomId = roomId;

            const requestParams = {
                room_id: roomId,
                start_dt: startDt.format('YYYY-MM-DDTHH:mm:ss'),
                end_dt: endDt.format('YYYY-MM-DDTHH:mm:ss')
            };

            $.ajax({
                url: build_url(Indico.Urls.RoomBooking.room.check_available, requestParams),
                method: 'GET',
                dataType: 'json',
                contentType: 'application/json',
                error: handleAjaxError,
                success(data) {
                    if (data['user_booking']) {
                        $createBooking.val(false);
                        $currentMessage = $userBookingMessage;
                    } else if (data['user_prebooking']) {
                        $createBooking.val(false);
                        $currentMessage = $userPrebookingMessage;
                    } else if (data['conflict_booking']) {
                        $createBooking.val(false);
                        $currentMessage = $conflictBookingMessage;
                    } else if (data['unbookable']) {
                        $createBooking.val(false);
                        $currentMessage = $unbookableMessage;
                    } else if (data['conflict_prebooking']) {
                        if (data['can_book']) {
                            $currentMessage = $conflictPrebookingMessage;
                        } else if (data['can_prebook']) {
                            $currentMessage = $conflictPrebookingPrebookMessage;
                        } else {
                            $currentMessage = $cantBookMessage;
                            $createBooking.val(false);
                        }
                    } else if (data['can_book']) {
                        $currentMessage = $availableMessage;
                    } else if (data['can_prebook']) {
                        $currentMessage = $availablePrebookMessage;
                    } else {
                        $currentMessage = $cantBookMessage;
                        $createBooking.val(false);
                    }
                    $currentMessage.show();
                }
            });
        }

        if (options.checkAvailability) {
            initAvailabilityValues();

            $('#event-creation-location_data').on('change', function() {
                roomData = JSON.parse($(this).val());
                if (previousRoomId !== roomData['room_id']) {
                    updateAvailability();
                }
            });

            $('#event-creation-start_dt-date').on('change', function() {
                const startDate = $(this).val();
                const startTime = $('#event-creation-start_dt-time').val();
                const endDate = $('#event-creation-end_dt-date').val();
                const endTime = $('#event-creation-end_dt-time').val();
                startDt = moment(`${startDate} ${startTime}`, 'DD/MM/YYYY HH:mm');
                endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
                // workaround for automatic end date update if start date is after end date
                if (endDt.isBefore(startDt)) {
                    endDt = moment(`${startDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
                }
                updateAvailability();
            });

            $('#event-creation-start_dt-time').on('change', function() {
                const startDate = $('#event-creation-start_dt-date').val();
                const startTime = $('#event-creation-start_dt-time').val();
                startDt = moment(`${startDate} ${startTime}`, 'DD/MM/YYYY HH:mm');
                updateAvailability();
            });

            $('#event-creation-end_dt-date').on('change', function() {
                const endDate = $(this).val();
                const endTime = $('#event-creation-end_dt-time').val();
                endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
                updateAvailability();
            });

            $('#event-creation-end_dt-time').on('change', function() {
                const endDate = $('#event-creation-end_dt-date').val();
                const endTime = $(this).val();
                endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
                updateAvailability();
            });

            $('#event-creation-occurrences').on('change', function() {
                const occurrences = JSON.parse($(this).val());
                if (occurrences.length === 1) {
                    setLectureTimes(occurrences[0]);
                    updateAvailability();
                } else {
                    $createBooking.val(false);
                    hideAvailability();
                }
            });

            $('#event-creation-timezone').on('change', function() {
                timezone = ($(this).val());
                updateAvailability();
            });

            $('#event-creation-category').on('change', function() {
                category = JSON.parse($(this).val());
                updateAvailability();
            });

            $('#create-booking').on('change', function() {
                $createBooking.val(this.checked);
            });

            $('#create-prebooking').on('change', function() {
                $createBooking.val(this.checked);
            });

            $('#create-booking-over-prebooking').on('change', function() {
                $createBooking.val(this.checked);
            });

            $('#create-prebooking-over-prebooking').on('change', function() {
                $createBooking.val(this.checked);
            });
        }
    };
})(window);
