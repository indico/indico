// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Link, NavLink, withRouter} from 'react-router-dom';
import {bindActionCreators} from 'redux';
import {Icon, Menu, Placeholder} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {selectors as mapSelectors} from '../../common/map';

import * as adminActions from './actions';
import * as adminSelectors from './selectors';

import './AdminMenu.module.scss';

function renderMenuPlaceholder() {
  return (
    <Menu vertical>
      <Menu.Item>
        <Menu.Header>
          <Placeholder>
            <Placeholder.Line length="medium" />
          </Placeholder>
        </Menu.Header>
        <Menu.Menu>
          <Menu.Item>
            <Placeholder>
              <Placeholder.Line length="short" />
              <Placeholder.Line length="short" />
              <Placeholder.Line length="short" />
              <Placeholder.Line length="short" />
            </Placeholder>
          </Menu.Item>
        </Menu.Menu>
      </Menu.Item>
    </Menu>
  );
}

function AdminMenu({locations, isFetchingLocations, isMapEnabled, actions: {clearTextFilter}}) {
  if (isFetchingLocations) {
    return renderMenuPlaceholder();
  }

  const hasLocations = locations.length !== 0;
  const locationURL = locationId => `/admin/locations/${locationId}`;
  return (
    <Menu size="large" styleName="admin-menu" vertical fluid>
      <Menu.Item>
        <NavLink exact to="/admin">
          <Translate>General Settings</Translate>
        </NavLink>
      </Menu.Item>
      {isMapEnabled && (
        <Menu.Item>
          <NavLink exact to="/admin/map-areas">
            <Translate>Map Areas</Translate>
          </NavLink>
        </Menu.Item>
      )}
      <Menu.Item>
        <Menu.Header>
          <Translate>Room Metadata</Translate>
        </Menu.Header>
        <Menu.Menu>
          <Menu.Item>
            <NavLink exact to="/admin/attributes">
              <Translate>Attributes</Translate>
            </NavLink>
          </Menu.Item>
          <Menu.Item>
            <NavLink exact to="/admin/equipment">
              <Translate>Equipment & Features</Translate>
            </NavLink>
          </Menu.Item>
        </Menu.Menu>
      </Menu.Item>
      <Menu.Item>
        <Link to="/admin/locations/">
          <Menu.Header styleName="locations-header">
            <Translate as="strong">Locations</Translate>
            <Icon name="setting" />
          </Menu.Header>
        </Link>
        {hasLocations && (
          <Menu.Menu>
            {locations.map(location => (
              <Menu.Item key={location.id}>
                <NavLink to={locationURL(location.id)} onClick={clearTextFilter} exact>
                  {location.name}
                </NavLink>
              </Menu.Item>
            ))}
          </Menu.Menu>
        )}
      </Menu.Item>
    </Menu>
  );
}

AdminMenu.propTypes = {
  locations: PropTypes.array.isRequired,
  isFetchingLocations: PropTypes.bool.isRequired,
  isMapEnabled: PropTypes.bool.isRequired,
  actions: PropTypes.exact({
    clearTextFilter: PropTypes.func.isRequired,
  }).isRequired,
};

export default withRouter(
  connect(
    state => ({
      locations: adminSelectors.getAllLocations(state),
      isMapEnabled: mapSelectors.isMapEnabled(state),
      isFetchingLocations: adminSelectors.isFetchingLocations(state),
    }),
    dispatch => ({
      actions: bindActionCreators(
        {
          clearTextFilter: adminActions.clearTextFilter,
        },
        dispatch
      ),
    })
  )(AdminMenu)
);
