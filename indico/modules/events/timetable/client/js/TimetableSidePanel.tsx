// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import './TimetableSidePanel.module.scss';
import {Icon, Menu, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';

export default function TimetableSidePanel() {
  const dispatch = useDispatch();
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const showSessions = useSelector(selectors.showSessions);

  return (
    <div styleName="side-panel">
      <Menu secondary vertical styleName="tab-rail">
        <Popup
          content={Translate.string('View sessions')}
          position="left center"
          size="small"
          trigger={
            <Menu.Item
              name="sessions"
              active={showSessions}
              onClick={() => dispatch(actions.toggleShowSessions())}
            >
              <Icon name="calendar outline" size="large" />
            </Menu.Item>
          }
        />

        <Popup
          content={Translate.string('View unscheduled contributions')}
          position="left center"
          size="small"
          trigger={
            <Menu.Item
              name="unscheduled"
              active={showUnscheduled}
              onClick={() => dispatch(actions.toggleShowUnscheduled())}
            >
              <Icon name="edit outline" size="large" />
            </Menu.Item>
          }
        />
      </Menu>
    </div>
  );
}
