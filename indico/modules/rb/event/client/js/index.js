// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import rbURL from 'indico-url:rb.roombooking';

import {serializeDate, serializeTime} from 'indico/utils/date';

$(document).ready(() => {
  $('#contribution, #session_block').on('change', e => {
    const $target = $(e.currentTarget);
    const objectId = $target.val();
    const $bookBtn = $target.closest('.searchable-field').find('.js-book-btn');
    const linkType = $target.data('link-type');
    let params = {};
    if (objectId) {
      const values = $target.closest('.searchable-field').data('values')[objectId];
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
