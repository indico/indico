// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import manageTagsURL from 'indico-url:event_editing.manage_tags';
import dashboardURL from 'indico-url:event_editing.dashboard';

import React from 'react';
import PropTypes from 'prop-types';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';
import {ManagementPageBackButton, ManagementPageSubTitle} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import EditingManagementDashboard from './EditingManagementDashboard';
import TagManager from './TagManager';

export default function EditingManagement({eventId}) {
  return (
    <Router>
      <Switch>
        <Route exact path={dashboardURL({confId: eventId})}>
          <EditingManagementDashboard eventId={eventId} />
        </Route>
        <Route exact path={manageTagsURL({confId: eventId})}>
          <ManagementPageBackButton url={dashboardURL({confId: eventId})} />
          <ManagementPageSubTitle title={Translate.string('Tags')} />
          <TagManager eventId={eventId} />
        </Route>
      </Switch>
    </Router>
  );
}

EditingManagement.propTypes = {
  eventId: PropTypes.number.isRequired,
};
