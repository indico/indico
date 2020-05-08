// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import manageTagsURL from 'indico-url:event_editing.manage_tags';
import dashboardURL from 'indico-url:event_editing.dashboard';
import editableTypeURL from 'indico-url:event_editing.manage_editable_type';
import editableListURL from 'indico-url:event_editing.manage_editable_type_list';
import manageFileTypesURL from 'indico-url:event_editing.manage_file_types';
import manageReviewConditionsURL from 'indico-url:event_editing.manage_review_conditions';

import React from 'react';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';
import {routerPathFromFlask} from 'indico/react/util/routing';

import EditingManagementDashboard from './EditingManagementDashboard';
import EditingTagManagement from './tags';
import {
  EditableTypeDashboard,
  FileTypeManagement,
  ReviewConditionsManagement,
  EditableList,
} from './editable_type';

export default function EditingManagement() {
  return (
    <Router>
      <Switch>
        <Route
          exact
          path={routerPathFromFlask(dashboardURL, ['confId'])}
          component={EditingManagementDashboard}
        />
        <Route
          exact
          path={routerPathFromFlask(manageTagsURL, ['confId'])}
          component={EditingTagManagement}
        />
        <Route
          exact
          path={routerPathFromFlask(editableTypeURL, ['confId', 'type'])}
          component={EditableTypeDashboard}
        />
        <Route
          exact
          path={routerPathFromFlask(manageFileTypesURL, ['confId', 'type'])}
          component={FileTypeManagement}
        />
        <Route
          exact
          path={routerPathFromFlask(manageReviewConditionsURL, ['confId', 'type'])}
          component={ReviewConditionsManagement}
        />
        <Route
          exact
          path={routerPathFromFlask(editableListURL, ['confId', 'type'])}
          component={EditableList}
        />
      </Switch>
    </Router>
  );
}
