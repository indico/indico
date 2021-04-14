// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'indico/legacy/angular';

import './invitations';
import './reglists';

import './form/form';
import './form/section';
import './form/field';
import './form/sectiontoolbar';
import './form/table';

import './form/templates';

(function(global) {
  $(document).ready(function() {
    setupRegistrationFormScheduleDialogs();
    setupRegistrationFormSummaryPage();
  });

  $(window).scroll(function() {
    IndicoUI.Effect.followScroll();
  });

  function setupRegistrationFormScheduleDialogs() {
    $('a.js-regform-schedule-dialog').on('click', function(e) {
      e.preventDefault();
      ajaxDialog({
        url: $(this).data('href'),
        title: $(this).data('title'),
        onClose: function(data) {
          if (data) {
            location.reload();
          }
        },
      });
    });
  }

  function setupRegistrationFormSummaryPage() {
    $('.js-check-conditions').on('click', function(e) {
      var conditions = $('#conditions-accepted');
      if (conditions.length && !conditions.prop('checked')) {
        var msg =
          'Please, confirm that you have read and accepted the Terms and Conditions before proceeding.';
        alertPopup($T.gettext(msg), $T.gettext('Terms and Conditions'));
        e.preventDefault();
      }
    });

    $('.js-highlight-payment').on('click', function() {
      $('#payment-summary').effect('highlight', 800);
    });
  }

  global.setupRegistrationFormListPage = function setupRegistrationFormListPage() {
    $('#payment-disabled-notice').on('indico:confirmed', '.js-enable-payments', function(evt) {
      evt.preventDefault();

      var $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function(data) {
          $('#payment-disabled-notice').remove();
          $('#event-side-menu').html(data.event_menu);
        },
      });
    });
  };
})(window);
