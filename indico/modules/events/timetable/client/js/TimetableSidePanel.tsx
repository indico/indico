// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import './TimetableSidePanel.module.scss';
import {Icon, Menu} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';
import {SidePanelView} from './types';

export default function TimetableSidePanel() {
  const dispatch = useDispatch();
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const showSessions = useSelector(selectors.showSessions);
  const activePanel = useSelector(selectors.getActivePanel);

  return (
    // TODO: (Marina) Rename to 'show draft entries' or something like that
    // once we have changed this sidemenu's features.
    <div styleName="side-panel">
      <Menu secondary vertical styleName="tab-rail">
        <Menu.Item
          name="sessions"
          active={showSessions}
          title={Translate.string('Sessions')}
          onClick={() =>
            dispatch(
              actions.setActivePanel(
                activePanel === SidePanelView.Sessions ? SidePanelView.None : SidePanelView.Sessions
              )
            )
          }
        >
          <Icon name="folder outline" size="large" />
        </Menu.Item>
        <Menu.Item
          name="unscheduled"
          active={showUnscheduled}
          title={Translate.string('Unscheduled contributions')}
          onClick={() =>
            dispatch(
              actions.setActivePanel(
                activePanel === SidePanelView.Unscheduled
                  ? SidePanelView.None
                  : SidePanelView.Unscheduled
              )
            )
          }
        >
          <Icon name="file outline" size="large" />
        </Menu.Item>
      </Menu>
    </div>
  );
}
