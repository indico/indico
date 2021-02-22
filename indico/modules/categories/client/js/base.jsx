// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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

  const userId = document.body.dataset.userId;
  const categoryId = calendarContainer.dataset.categoryId;

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="categories.export_ical"
      urlParams={{user_id: userId, category_id: categoryId}}
      renderButton={onClick => <IButton icon="calendar" onClick={onClick} />}
      options={[{key: 'category', text: Translate.string('Category'), queryParams: {}}]}
    />,
    calendarContainer
  );
});
