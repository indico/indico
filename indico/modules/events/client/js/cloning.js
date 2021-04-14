// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  global.setupCloneDialog = function setupCloneDialog() {
    const $formContainer = $('#event-clone-form-container');
    const $form = $('#event-clone-form');
    const $eventCount = $('#event-count').hide();
    const $eventList = $form.find('.event-list');
    const $cloneErrors = $('#clone-errors').hide();
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

    const updateCount = _.debounce(function(force) {
      const $cloneButton = $('.clone-action-button');
      const serializedForm = $.param($form.serializeArray(), true);

      // make sure the form was actually changed
      if (!force && serializedForm === $form.data('initialData')) {
        return;
      }

      // set 'intiialData' by hand here, so that the if we're in a 'keyup'
      // event, the successive 'change' event will receive the updated version
      $form.data('initialData', serializedForm);

      $form.ajaxSubmit({
        url: $formContainer.data('preview-url'),
        method: 'POST',
        success(data) {
          if (data.success) {
            const $countNumber = $eventCount.find('.count');
            const $lastDay = $eventCount.find('.last-day');
            $countNumber.text(data.count);
            $cloneErrors.hide();
            $eventCount.show();
            $eventList.toggle(!!data.count);
            $cloneButton.prop('disabled', !data.count);
            $eventCount.data('event-dates', data.dates);
            $lastDay.toggle(data.last_day_of_month);
          } else {
            $cloneErrors
              .show()
              .find('.message-text')
              .html(errorToHTML(data.error.message));
            $eventCount.hide();
          }
        },
      });
    }, 300);

    if (step === 4) {
      $form.on('change', 'select, input', _.partial(updateCount, false));
      $form.on('keyup', 'input', function(e) {
        e.preventDefault();
        updateCount(false);
      });
    }

    if ($eventCount.length) {
      _.defer(_.partial(updateCount, true));
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

    $eventList.qtip({
      style: {
        classes: 'cloned-event-list-qtip',
      },
      show: {
        event: 'click',
      },
      content() {
        const $ul = $('<ul>');
        const events = $eventCount.data('event-dates').map(function(item) {
          return $('<li>').text(moment(item.date).format('ddd L'));
        });
        $ul.append(events.slice(0, 20));
        if (events.length > 20) {
          $ul.append('<li>...</li>');
        }
        return $ul;
      },
    });
  };
})(window);
