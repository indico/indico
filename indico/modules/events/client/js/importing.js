// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {serializeDateTimeRange} from 'indico/utils/date';

(function(global) {
  global.setupImportDialog = function setupImportDialog() {
    const $formContainer = $('#event-import-form-container');
    const $form = $('#event-import-form');
    const $eventDetails = $('#event-details').hide();
    const $cloneErrors = $('#clone-errors').hide();
    const $nextButton = $('.clone-action-button');
    const step = $formContainer.data('step');
    const clonerDependencies = $formContainer.data('clonerDependencies');

    function errorToHTML(error) {
      if (typeof error === 'string') {
        return error;
      } else {
        return $('<div>').append(
          error.map(function(item) {
            const label = $('<strong>').append(item[0]);
            const items = $('<ul>').append(
              item[1].map(function(message) {
                return $('<li>').text(message);
              })
            );
            return $('<div>').append(label, items);
          })
        );
      }
    }

    const updateEventDetails = _.debounce(function(force) {
      const serializedForm = $.param($form.serializeArray(), true);

      // make sure the form was actually changed
      if (!force && serializedForm === $form.data('initialData')) {
        return;
      }

      // set 'intiialData' by hand here, so that the if we're in a 'keyup'
      // event, the successive 'change' event will receive the updated version
      $form.data('initialData', serializedForm);

      $form.ajaxSubmit({
        url: $formContainer.data('event-details-url'),
        method: 'POST',
        success(data) {
          if (data.success) {
            const $eventTitle = $eventDetails.find('.import-event-title');
            const $eventCategory = $eventDetails.find('.import-event-category');
            const $eventDates = $eventDetails.find('.import-event-dates');
            $eventTitle.text(data.event.title);
            $eventCategory.text(data.event.category_chain.join(' » '));
            $eventDates.text(serializeDateTimeRange(data.event.start_dt, data.event.end_dt));
            $cloneErrors.hide();
            $eventDetails.show();
            $nextButton.prop('disabled', false);
          } else {
            $cloneErrors
              .show()
              .find('.message-text')
              .html(errorToHTML(data.error.message));
            $eventDetails.hide();
            $nextButton.prop('disabled', true);
          }
        },
      });
    }, 300);

    if (step === 1) {
      $nextButton.prop('disabled', true);
      $form.on('change', 'input', _.partial(updateEventDetails, false));
      $form.on('keyup', 'input', function(e) {
        e.preventDefault();
        updateEventDetails(false);
      });
    }

    if (step === 2) {
      $form.find('#form-group-selected_items').on('change', 'input[type=checkbox]', function() {
        const $this = $(this);
        const dependencies = clonerDependencies[$this.val()];
        const $field = $this.closest('.form-field');

        if ($this.prop('checked')) {
          if (dependencies.requires) {
            dependencies.requires.forEach(function(optionName) {
              $field.find('[value={0}]:not(:disabled)'.format(optionName)).prop('checked', true);
            });
          }
        } else if (dependencies.required_by) {
          dependencies.required_by.forEach(function(optionName) {
            $field.find('[value={0}]'.format(optionName)).prop('checked', false);
          });
        }
      });

      // first check requirements of checked items
      $('#form-group-selected_items input[type=checkbox]:checked').trigger('change');
      // then ensure that nothing is checked that shouldn't be checked
      $('#form-group-selected_items input[type=checkbox]:not(:checked)').trigger('change');
    }
  };
})(window);
