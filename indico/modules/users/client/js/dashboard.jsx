// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {ICSCalendarLink} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

document.addEventListener('DOMContentLoaded', () => {
  ReactDOM.render(
    <ICSCalendarLink
      endpoint="users.export_dashboard_ics"
      options={[
        {key: 'events', text: Translate.string('Events at hand'), extraParams: {include: 'linked'}},
        {
          key: 'categories',
          text: Translate.string('Categories'),
          extraParams: {include: 'categories'},
        },
        {key: 'everything', text: Translate.string('Everything'), extraParams: {}},
      ]}
    />,
    document.querySelector('#dashboard-calendar-link')
  );
});
