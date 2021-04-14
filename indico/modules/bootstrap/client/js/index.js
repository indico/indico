// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// eslint-disable-next-line import/unambiguous
$(document).ready(function() {
  // Header shrinking function
  $(window).scroll(function() {
    if (
      $(window).scrollTop() >= $('.bootstrap-header').outerHeight() / 2 &&
      !$('.bootstrap-header').hasClass('mini')
    ) {
      $('.bootstrap-header').addClass('mini');
      $('.bootstrap-body').addClass('mini');
      $(window).scrollTop(0);
    }
  });

  // Instance Tracking slider
  const toggleCheckbox = $('#form-group-enable_tracking input:checkbox');
  toggleCheckbox.on('change', function() {
    const $this = $(this);
    const enabled = $this.prop('checked');
    const itEmail = $('#contact_email');
    const itContact = $('#contact_name');
    const firstName = $('#first_name').val();
    const lastName = $('#last_name').val();
    const name = !!firstName && !!lastName ? '{0} {1}'.format(firstName, lastName) : '';

    itEmail.prop('required', enabled);
    itEmail.prop('disabled', !enabled);
    if (!itEmail.val()) {
      itEmail.val($('#email').val());
      itEmail.trigger('input');
    }
    itContact.prop('required', enabled);
    itContact.prop('disabled', !enabled);
    if (!itContact.val() && !!name) {
      itContact.val(name);
      itContact.trigger('input');
    }
  });
  toggleCheckbox.trigger('change');
});
