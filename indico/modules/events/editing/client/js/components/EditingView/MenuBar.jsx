// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import managementURL from 'indico-url:event_management.settings';
import displayURL from 'indico-url:events.display';

import React from 'react';
import PropTypes from 'prop-types';
import {Header, Icon} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import './MenuBar.module.scss';

export default function MenuBar({eventId, eventTitle, menuItems}) {
  return (
    <div styleName="menu-bar">
      <Header as="h2" styleName="header">
        Paper Editing
      </Header>
      <ul styleName="list">
        <li>
          <Translate>OTHER MODULES</Translate>
          <ul styleName="inner-list">
            <a href="#">
              <li styleName="inner-list-item">
                <Translate>Call for Papers</Translate>
              </li>
            </a>
            <a href="#">
              <li styleName="inner-list-item">
                <Translate>Call for Abstracts</Translate>
              </li>
            </a>
          </ul>
        </li>
      </ul>
      <ul styleName="list">
        <li>
          <Translate>OTHER VIEWS</Translate>
          <ul styleName="inner-list">
            <a href={displayURL({confId: eventId})}>
              <li styleName="inner-list-item">
                <Icon name="tv" />
                <Translate>Display</Translate>
              </li>
            </a>
            <a href={managementURL({confId: eventId})}>
              <li styleName="inner-list-item">
                <Icon name="pencil" />
                <Translate>Management</Translate>
              </li>
            </a>
          </ul>
        </li>
      </ul>
    </div>
  );
}

MenuBar.propTypes = {
  eventId: PropTypes.number.isRequired,
  eventTitle: PropTypes.string.isRequired,
  menuItems: PropTypes.array.isRequired,
};
