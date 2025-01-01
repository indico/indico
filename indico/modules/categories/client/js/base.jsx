// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {IButton, ICSCalendarLink} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

document.addEventListener('DOMContentLoaded', () => {
  const calendarContainer = document.querySelector('#category-calendar-link');

  if (!calendarContainer) {
    return;
  }

  const categoryId = calendarContainer.dataset.categoryId;

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="categories.export_ical"
      params={{category_id: categoryId}}
      renderButton={classes => (
        <IButton icon="calendar" title={Translate.string('Export')} classes={classes} />
      )}
      options={[{key: 'category', text: Translate.string('Category'), extraParams: {}}]}
    />,
    calendarContainer
  );
});
