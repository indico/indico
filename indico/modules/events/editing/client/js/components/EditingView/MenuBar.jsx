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
            {menuItems.map(item => (
              <a key={item.name} href={item.url}>
                <li styleName="inner-list-item">{item.title}</li>
              </a>
            ))}
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

const menuEntryPropTypes = {
  name: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  weight: PropTypes.number.isRequired,
  active: PropTypes.bool.isRequired,
  disabled: PropTypes.bool.isRequired,
  section: PropTypes.string.isRequired,
  icon: PropTypes.string,
};
MenuBar.propTypes = {
  eventId: PropTypes.number.isRequired,
  eventTitle: PropTypes.string.isRequired,
  menuItems: PropTypes.arrayOf(PropTypes.shape(menuEntryPropTypes)).isRequired,
};
