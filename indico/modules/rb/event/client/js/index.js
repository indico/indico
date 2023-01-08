// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import rbURL from 'indico-url:rb.roombooking';

import {serializeDate, serializeTime} from 'indico/utils/date';

$(document).ready(() => {
  $('#contribution-data, #session_block-data').on('change', e => {
    const $target = $(e.currentTarget);
    const $fieldContainer = $target.closest('.searchable-field');
    const objectId = $target.val();
    const $bookBtn = $fieldContainer.find('.js-book-btn');
    const linkType = $target.data('link-type');
    let params = {};
    if (objectId) {
      const values = $fieldContainer.data('values')[objectId];
      params = {
        link_type: linkType,
        link_id: objectId,
        recurrence: 'single',
        number: 1,
        interval: 'week',
        sd: serializeDate(values.start_dt),
        st: serializeTime(values.start_dt),
        et: serializeTime(values.end_dt),
      };
    }
    $bookBtn.toggleClass('disabled', !objectId).attr('href', rbURL({path: 'book', ...params}));
  });
});
