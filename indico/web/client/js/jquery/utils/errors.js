// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import showReactErrorDialog from 'indico/react/errors';
import {$T} from 'indico/utils/i18n';

(function(global) {
  global.handleAjaxError = function handleAjaxError(data) {
    if (
      'responseText' in data &&
      data.readyState === 0 &&
      data.status === 0 &&
      !data.responseText
    ) {
      // if data is an XHR object and we don't have any readyState, status or response text
      // the request most likely failed due to a page change so we just ignore the failure.
      // this is not 100% reliable, an interrupted connection could yield the same result.
      // since showing an error dialog in that case won't be very useful either this drawback
      // is acceptable.
      return true;
    }
    if (data.responseText) {
      // $.ajax error callback, so data is the xhr object
      try {
        data = JSON.parse(data.responseText);
      } catch (e) {
        showReactErrorDialog({
          title: $T.gettext('Something went wrong'),
          message: '{0} ({1})'.format(data.statusText.toLowerCase(), data.status),
        });
        return true;
      }
    }
    // data.data.error is only needed for angular error handlers
    const error = data.error || (data.data && data.data.error);
    if (error) {
      showReactErrorDialog(error);
      return true;
    }
  };

  function appendToken(value, token) {
    return [...new Set(`${value || ''} ${token}`.trim().split(/\s+/))].join(' ');
  }

  function getFieldErrorId(field, input) {
    const fieldId = input.attr('id') || field.closest('.form-group').attr('id') || field.index();
    return `${fieldId}-error`;
  }

  function describeFormError(field, input) {
    const errorId = getFieldErrorId(field, input);
    let error = field.children(`#${$.escapeSelector(errorId)}`);

    if (!error.length) {
      error = $('<div>', {
        id: errorId,
        class: 'form-field-error-message',
        role: 'alert',
      }).appendTo(field);
    }

    error.html(field.data('error'));
    input.attr({
      'aria-invalid': 'true',
      'aria-describedby': appendToken(input.attr('aria-describedby'), errorId),
    });
  }

  // Select the field of an i-form which has an error and display the tooltip.
  global.showFormErrors = function showFormErrors(context) {
    context = context || $('body');
    context
      .find('.i-form .has-error > .form-field, .i-form .has-error > .form-subfield')
      .each(function() {
        const $this = $(this);
        // Try a custom tooltip anchor
        let input = $this.find('[data-tooltip-anchor]');

        if (!input.length) {
          // Try the first non-hidden input field
          input = $this.children(':input:not(:hidden)').eq(0);
        }

        if (!input.length) {
          // Try the first native or custom focusable field.
          input = $this
            .children('input, select, textarea, button, [tabindex], [contenteditable]')
            .eq(0);
        }

        if (!input.length) {
          // Try the first element that's not a hidden input
          input = $this.children(':not(:input:hidden)').eq(0);
        }
        input.stickyTooltip('danger', () => $this.data('error'));
        describeFormError($this, input);
      });
  };
})(window);
