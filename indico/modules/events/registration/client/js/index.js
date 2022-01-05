// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global $T:false, alertPopup:false, handleAjaxError:false, ajaxDialog:false */

import React from 'react';
import ReactDOM from 'react-dom';

import 'indico/legacy/angular';

import './invitations';
import './reglists';

import './form/form';
import './form/section';
import './form/field';
import './form/sectiontoolbar';
import './form/table';

import './form/templates';

import RegistrationTagsEditableList from './components/RegistrationTagsEditableList';

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
        onClose(data) {
          if (data) {
            location.reload();
          }
        },
      });
    });
  }

  function setupRegistrationFormSummaryPage() {
    $('.js-check-conditions').on('click', function(e) {
      const conditions = $('#conditions-accepted');
      if (conditions.length && !conditions.prop('checked')) {
        const msg =
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

      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          $('#payment-disabled-notice').remove();
          $('#event-side-menu').html(data.event_menu);
        },
      });
    });
  };

  function setupRegistrationTags() {
    const rootElement = document.getElementById('registration-detail-registration-tags-assign');

    if (rootElement) {
      const assignedTags = JSON.parse(rootElement.dataset.assignedTags);
      const allTags = JSON.parse(rootElement.dataset.allTags);
      const {eventId, regformId, registrationId} = rootElement.dataset;

      ReactDOM.render(
        <RegistrationTagsEditableList
          eventId={parseInt(eventId, 10)}
          regformId={parseInt(regformId, 10)}
          registrationId={parseInt(registrationId, 10)}
          assignedTags={assignedTags}
          allTags={allTags}
        />,
        rootElement
      );
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupRegistrationTags();
    $('#registration-details')
      .parent()
      .on('indico:htmlUpdated', setupRegistrationTags);
  });
})(window);
