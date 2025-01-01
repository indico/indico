// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import dashboardURL from 'indico-url:event_editing.dashboard';
import editableTypeURL from 'indico-url:event_editing.manage_editable_type';
import editableListURL from 'indico-url:event_editing.manage_editable_type_list';
import manageFileTypesURL from 'indico-url:event_editing.manage_file_types';
import manageReviewConditionsURL from 'indico-url:event_editing.manage_review_conditions';
import manageTagsURL from 'indico-url:event_editing.manage_tags';

import React from 'react';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';

import {routerPathFromFlask} from 'indico/react/util/routing';

import {
  EditableTypeDashboard,
  FileTypeManagement,
  ReviewConditionsManagement,
  EditableList,
} from './editable_type';
import EditingManagementDashboard from './EditingManagementDashboard';
import EditingTagManagement from './tags';

export default function EditingManagement() {
  return (
    <Router>
      <Switch>
        <Route
          exact
          path={routerPathFromFlask(dashboardURL, ['event_id'])}
          component={EditingManagementDashboard}
        />
        <Route
          exact
          path={routerPathFromFlask(manageTagsURL, ['event_id'])}
          component={EditingTagManagement}
        />
        <Route
          exact
          path={routerPathFromFlask(editableTypeURL, ['event_id', 'type'])}
          component={EditableTypeDashboard}
        />
        <Route
          exact
          path={routerPathFromFlask(manageFileTypesURL, ['event_id', 'type'])}
          component={FileTypeManagement}
        />
        <Route
          exact
          path={routerPathFromFlask(manageReviewConditionsURL, ['event_id', 'type'])}
          component={ReviewConditionsManagement}
        />
        <Route
          exact
          path={routerPathFromFlask(editableListURL, ['event_id', 'type'])}
          component={EditableList}
        />
      </Switch>
    </Router>
  );
}
