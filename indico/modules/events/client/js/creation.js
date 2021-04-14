// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global handleAjaxError:false */

import moment from 'moment';
import rbURL from 'indico-url:rb.roombooking';
import checkRoomAvailabilityURL from 'indico-url:rb.check_room_available';

import {camelizeKeys} from 'indico/utils/case';

/* eslint-disable import/unambiguous */
(function(global) {
  global.setupEventCreationDialog = function setupEventCreationDialog(options) {
    options = $.extend(
      {
        categoryField: null,
        protectionModeFields: null,
        initialCategory: null,
        checkAvailability: false,
        rbExcludedCategories: null,
        serverDefaultTimezone: null,
      },
      options
    );

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
    const $cannotBookMessage = $('#room-cannot-book');
    const $bookingSwitch = $('#create-booking');
    const $prebookingSwitch = $('#create-prebooking');
    const $bookingSwitchPrebooking = $('#create-booking-over-prebooking');
    const $prebookingSwitchPrebooking = $('#create-prebooking-over-prebooking');

    let currentCategory = null;
    let previousRoomId, $currentMessage, startDt, endDt, category, roomData, timezone;
    let multipleOccurrences = false;

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
      startDt = moment(`${occurrence['date']} ${occurrence['time']}`, 'YYYY-MM-DD HH:mm');
      endDt = moment(startDt).add(occurrence['duration'], 'minutes');
    }

    function initAvailabilityValues() {
      const startDate = $('#event-creation-start_dt-datestorage').val();
      const startTime = $('#event-creation-start_dt-timestorage').val();
      const endDate = $('#event-creation-end_dt-datestorage').val();
      const endTime = $('#event-creation-end_dt-timestorage').val();
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
      return options.rbExcludedCategories.some(excludedCategory => {
        return parseInt(excludedCategory.id, 10) === categoryId;
      });
    }

    function addCalendarLink($message) {
      const params = {
        path: 'calendar',
        date: startDt.format('YYYY-MM-DD'),
        text: roomData['room_name'],
      };
      const url = rbURL(params);
      $message.find('a').prop('href', url);
    }

    function hideAvailability(resetCheckbox) {
      if ($currentMessage) {
        if (resetCheckbox) {
          $('#availability-messages')
            .find("input[id^='create']")
            .prop('checked', false);
          $createBooking.val('false');
        }
        $currentMessage.hide();
      }
    }

    function updateAvailability(resetCheckbox = false) {
      hideAvailability(resetCheckbox);

      if (
        !('room_id' in roomData) ||
        !startDt.isValid() ||
        !endDt.isValid() ||
        !startDt.isSame(endDt, 'day') ||
        startDt.isSameOrAfter(endDt) ||
        isCategoryExcluded(category['id']) ||
        timezone !== options.serverDefaultTimezone ||
        multipleOccurrences
      ) {
        $createBooking.val('false');
        return;
      }

      const requestParams = {
        room_id: roomData['room_id'],
        start_dt: startDt.format(moment.HTML5_FMT.DATETIME_LOCAL),
        end_dt: endDt.format(moment.HTML5_FMT.DATETIME_LOCAL),
      };

      $.ajax({
        url: checkRoomAvailabilityURL(requestParams),
        method: 'GET',
        dataType: 'json',
        contentType: 'application/json',
        error: handleAjaxError,
        success(data) {
          data = camelizeKeys(data);
          if (data.userBooking) {
            $createBooking.val('false');
            $currentMessage = $userBookingMessage;
            addCalendarLink($currentMessage);
          } else if (data.userPrebooking) {
            $createBooking.val('false');
            $currentMessage = $userPrebookingMessage;
            addCalendarLink($currentMessage);
          } else if (data.conflictBooking) {
            $createBooking.val('false');
            $currentMessage = $conflictBookingMessage;
            addCalendarLink($currentMessage);
          } else if (data.unbookable) {
            $createBooking.val('false');
            $currentMessage = $unbookableMessage;
            addCalendarLink($currentMessage);
          } else if (data.conflictPrebooking) {
            if (data.canBook) {
              $createBooking.val(String($bookingSwitchPrebooking[0].checked));
              $currentMessage = $conflictPrebookingMessage;
              addCalendarLink($currentMessage);
            } else if (data.canPrebook) {
              $createBooking.val(String($prebookingSwitchPrebooking[0].checked));
              $currentMessage = $conflictPrebookingPrebookMessage;
              addCalendarLink($currentMessage);
            } else {
              $createBooking.val('false');
              $currentMessage = $cannotBookMessage;
            }
          } else if (data.canBook) {
            $createBooking.val(String($bookingSwitch[0].checked));
            $currentMessage = $availableMessage;
          } else if (data.canPrebook) {
            $createBooking.val(String($prebookingSwitch[0].checked));
            $currentMessage = $availablePrebookMessage;
          } else {
            $createBooking.val('false');
            $currentMessage = $cannotBookMessage;
          }
          $currentMessage.show();
        },
      });
    }

    if (options.checkAvailability) {
      initAvailabilityValues();

      $('#event-creation-location_data').on('change', function() {
        roomData = JSON.parse($(this).val());
        if (previousRoomId !== roomData['room_id']) {
          previousRoomId = roomData['room_id'];
          updateAvailability(true);
        }
      });

      $('#event-creation-start_dt-datestorage').on('change', function() {
        const startDate = $(this).val();
        const startTime = $('#event-creation-start_dt-timestorage').val();
        const endDate = $('#event-creation-end_dt-datestorage').val();
        const endTime = $('#event-creation-end_dt-timestorage').val();
        startDt = moment(`${startDate} ${startTime}`, 'DD/MM/YYYY HH:mm');
        endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
        // workaround for automatic end date update if start date is after end date
        if (endDt.isBefore(startDt)) {
          endDt = moment(`${startDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
        }
        updateAvailability();
      });

      $('#event-creation-start_dt-timestorage').on('change', function() {
        const startDate = $('#event-creation-start_dt-datestorage').val();
        const startTime = $('#event-creation-start_dt-timestorage').val();
        startDt = moment(`${startDate} ${startTime}`, 'DD/MM/YYYY HH:mm');
        updateAvailability();
      });

      $('#event-creation-end_dt-datestorage').on('change', function() {
        const endDate = $(this).val();
        const endTime = $('#event-creation-end_dt-timestorage').val();
        endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
        updateAvailability();
      });

      $('#event-creation-end_dt-timestorage').on('change', function() {
        const endDate = $('#event-creation-end_dt-datestorage').val();
        const endTime = $(this).val();
        endDt = moment(`${endDate} ${endTime}`, 'DD/MM/YYYY HH:mm');
        updateAvailability();
      });

      $('#event-creation-occurrences').on('change', function() {
        const occurrences = JSON.parse($(this).val());
        if (occurrences.length === 1) {
          setLectureTimes(occurrences[0]);
          multipleOccurrences = false;
        } else {
          multipleOccurrences = true;
        }
        updateAvailability();
      });

      $('#event-creation-timezone').on('change', function() {
        timezone = $(this).val();
        updateAvailability();
      });

      $('#event-creation-category').on('change', function() {
        category = JSON.parse($(this).val());
        updateAvailability();
      });

      $bookingSwitch
        .add($prebookingSwitch)
        .add($bookingSwitchPrebooking)
        .add($prebookingSwitchPrebooking)
        .on('change', function() {
          $createBooking.val(String(this.checked));
        });
    }
  };
})(window);
