// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global $T:false, alertPopup:false, handleAjaxError:false, ajaxDialog:false */

import setupRegformSetup from './form_setup';
import setupRegformSubmission from './form_submission';
import ConsentToPublishEditor from './components/ConsentToPublishEditor';


(function(global) {
  document.addEventListener('DOMContentLoaded', () => {
    const setupRootElement = document.getElementById('registration-form-setup-container');
    if (setupRootElement) {
      setupRegformSetup(setupRootElement);
    }
    const submissionRootElement = document.getElementById('registration-form-submission-container');
    if (submissionRootElement) {
      setupRegformSubmission(submissionRootElement);
    }
  });
  function setupConsentToPublish() {
    const rootElement = document.getElementById('registration-summary-consent-to-publish');

    if (rootElement) {
      const {locator, publishToParticipants, publishToPublic, initialConsentToPublish} =
        rootElement.dataset;

      ReactDOM.render(
        <ConsentToPublishEditor
          locator={JSON.parse(locator)}
          publishToParticipants={publishToParticipants}
          publishToPublic={publishToPublic}
          initialConsentToPublish={initialConsentToPublish}
        />,
        rootElement
      );
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupConsentToPublish();
    $('#registration-info').parent().on('indico:htmlUpdated', setupConsentToPublish);
  });
})(window);
