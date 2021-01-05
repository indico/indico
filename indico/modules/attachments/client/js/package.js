// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global handleFlashes:false, handleAjaxError:false */

import packageStatusURL from 'indico-url:attachments.package_status';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {$T} from 'indico/utils/i18n';

window.setupGeneratePackage = function setupGeneratePackage(eventId) {
  $('#filter_type input:radio').on('change', function() {
    $('#form-group-sessions').toggle(this.value === 'sessions');
    $('#form-group-contributions').toggle(this.value === 'contributions');
    $('#form-group-dates').toggle(this.value === 'dates');
  });
  $('#filter_type input:radio:checked').trigger('change');

  const $form = $('#download-package-form');
  let closeLoader;

  async function poll(taskId) {
    let res;
    try {
      res = await indicoAxios.get(packageStatusURL({confId: eventId, task_id: taskId}));
    } catch (error) {
      handleAxiosError(error);
      closeLoader();
      return;
    }
    if (res.data.download_url) {
      window.location.href = res.data.download_url;
      closeLoader();
    } else {
      poll(taskId);
    }
  }

  $form.ajaxForm({
    error(...args) {
      closeLoader();
      handleAjaxError(...args);
    },
    beforeSubmit() {
      closeLoader = IndicoUI.Dialogs.Util.progress($T.gettext('Building package'));
    },
    success(data) {
      if (data.success) {
        poll(data.task_id);
      } else {
        handleFlashes(data, true, $form.find('.flashed-messages'));
        closeLoader();
      }
    },
  });
};
