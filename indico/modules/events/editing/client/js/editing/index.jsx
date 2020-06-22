// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import timelineURL from 'indico-url:event_editing.editable';
import editableTypeListURL from 'indico-url:event_editing.editable_type_list';

import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';
import {routerPathFromFlask} from 'indico/react/util/routing';

import EditingView from './page_layout';
import ReduxTimeline from './ReduxTimeline';
import {EditableList} from '../management/editable_type';

document.addEventListener('DOMContentLoaded', async () => {
  const editingElement = document.querySelector('#editing-view');

  if (!editingElement) {
    return;
  }

  const headerHeight =
    document.querySelector('div.header').getBoundingClientRect().height +
    document.querySelector('div.main-breadcrumb').getBoundingClientRect().height;
  document.body.style.setProperty('--header-height', headerHeight);

  const eventTitle = editingElement.dataset.eventTitle;

  ReactDOM.render(
    <Router>
      <Route
        path={[
          routerPathFromFlask(timelineURL, ['confId', 'contrib_id', 'type']),
          routerPathFromFlask(editableTypeListURL, ['confId', 'type']),
        ]}
      >
        <EditingView eventTitle={eventTitle}>
          <Switch>
            <Route
              exact
              path={routerPathFromFlask(timelineURL, ['confId', 'contrib_id', 'type'])}
              component={ReduxTimeline}
            />
            <Route exact path={routerPathFromFlask(editableTypeListURL, ['confId', 'type'])}>
              <EditableList management={false} />
            </Route>
          </Switch>
        </EditingView>
      </Route>
    </Router>,
    editingElement
  );
});
