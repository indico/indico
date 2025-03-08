// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationPermissionInfoURL from 'indico-url:rb.location_permission_types';

import createDecorator from 'final-form-calculate';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {List} from 'semantic-ui-react';

import {ACLField} from 'indico/react/components';
import {PermissionInfoProvider} from 'indico/react/components/principals/hooks';
import {validators as v, FinalDropdown, FinalInput, FinalField} from 'indico/react/forms';
import {FavoritesProvider} from 'indico/react/hooks';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {snakifyKeys} from 'indico/utils/case';

import {selectors as userSelectors} from '../../common/user';

import * as adminActions from './actions';
import EditableList from './EditableList';
import * as adminSelectors from './selectors';

import './EditableList.module.scss';

const MAP_TEMPLATE_OPTIONS = [
  {
    value: 'none',
    text: Translate.string('None', 'Map template'),
  },
  {
    value: 'custom',
    text: Translate.string('Custom', 'Map template'),
  },
  {
    value: 'https://www.google.com/maps/place/{lat},{lng}',
    text: 'Google Maps',
  },
  {
    value: 'https://www.openstreetmap.org/?mlat={lat}&mlon={lng}&zoom=18',
    text: 'OpenStreetMap',
  },
];

const formDecorator = createDecorator({
  field: '_map_url_template_choice',
  updates: value => {
    if (value !== 'custom') {
      return {map_url_template: value === 'none' ? null : value};
    }
    return {};
  },
});

class LocationPage extends React.PureComponent {
  static propTypes = {
    locations: PropTypes.array.isRequired,
    isFetching: PropTypes.bool.isRequired,
    canAddItem: PropTypes.bool.isRequired,
    actions: PropTypes.exact({
      fetchLocations: PropTypes.func.isRequired,
      deleteLocation: PropTypes.func.isRequired,
      updateLocation: PropTypes.func.isRequired,
      createLocation: PropTypes.func.isRequired,
    }).isRequired,
  };

  componentDidMount() {
    const {
      isFetching,
      actions: {fetchLocations},
    } = this.props;
    if (!isFetching) {
      fetchLocations();
    }
  }

  renderItem = ({name, numRooms}) => (
    <List.Content styleName="info">
      <List.Header>
        <span styleName="name">{name}</span>
      </List.Header>
      <List.Description>
        {!numRooms ? (
          <Translate>No rooms</Translate>
        ) : (
          <PluralTranslate count={numRooms}>
            <Singular>
              <Param name="count" wrapper={<strong />}>
                1
              </Param>{' '}
              room
            </Singular>
            <Plural>
              <Param name="count" wrapper={<strong />} value={numRooms} /> rooms
            </Plural>
          </PluralTranslate>
        )}
      </List.Description>
    </List.Content>
  );

  renderForm = () => (
    <>
      <FinalInput name="name" required label={Translate.string('Name')} autoFocus />
      <FinalInput
        name="room_name_format"
        required
        label={Translate.string('Room name format')}
        validate={val => {
          const rv = v.required(val);
          if (rv) {
            return rv;
          }
          if (!val.includes('{number}')) {
            return Translate.string('Missing placeholder: number');
          }
          const validPlaceholders = ['{site}', '{building}', '{floor}', '{number}'];
          const placeholders = [...val.matchAll(/\{.*?\}/g)].map(match => match[0]);
          const invalid = placeholders.filter(ph => !validPlaceholders.includes(ph));
          if (invalid.length) {
            return PluralTranslate.string(
              'Invalid placeholder: {placeholders}',
              'Invalid placeholders: {placeholders}',
              invalid.length,
              {placeholders: invalid.join(', ')}
            );
          }
        }}
        description={
          <Translate>
            Specify the room name format using any of the following placeholders:{' '}
            <Param
              name="placeholders"
              wrapper={<code />}
              value="{site}, {building}, {floor}, {number}"
            />
          </Translate>
        }
      />
      <FinalDropdown
        name="_map_url_template_choice"
        label={Translate.string('Map URL template')}
        description={
          <Translate>
            Indico can show a link to an external map when a room is associated to an event.
          </Translate>
        }
        selection
        options={MAP_TEMPLATE_OPTIONS}
      />
      <Field name="_map_url_template_choice" subscription={{value: true}}>
        {({input: {value: selectedTemplate}}) => (
          <FinalInput
            name="map_url_template"
            label=""
            readOnly={selectedTemplate !== 'custom'}
            style={selectedTemplate === 'none' ? {display: 'none'} : {}}
            nullIfEmpty
            validate={val => {
              if (!val) {
                return;
              }
              const rv = v.url(val);
              if (rv) {
                return rv;
              }
              const validPlaceholders = [
                '{id}',
                '{building}',
                '{floor}',
                '{number}',
                '{lat}',
                '{lng}',
              ];
              const placeholders = [...val.matchAll(/\{.*?\}/g)].map(match => match[0]);
              const invalid = placeholders.filter(ph => !validPlaceholders.includes(ph));
              if (invalid.length) {
                return PluralTranslate.string(
                  'Invalid placeholder: {placeholders}',
                  'Invalid placeholders: {placeholders}',
                  invalid.length,
                  {placeholders: invalid.join(', ')}
                );
              }
            }}
            description={
              selectedTemplate === 'custom' && (
                <Translate>
                  Specify a custom URL template using any of the following placeholders:{' '}
                  <Param
                    name="placeholders"
                    wrapper={<code />}
                    value="{id}, {building}, {floor}, {number}, {lat}, {lng}"
                  />
                </Translate>
              )
            }
          />
        )}
      </Field>
      <FavoritesProvider>
        {favoriteUsersController => (
          <PermissionInfoProvider url={locationPermissionInfoURL()}>
            {(permissionManager, permissionInfo) => (
              <div style={{marginBottom: '20px'}}>
                {permissionManager && permissionInfo && (
                  <FinalField
                    name="acl_entries"
                    component={ACLField}
                    favoriteUsersController={favoriteUsersController}
                    label={Translate.string('Permissions')}
                    permissions={false}
                    readAccessAllowed={false}
                    isEqual={_.isEqual}
                    withGroups
                    permissionInfo={permissionInfo}
                    permissionManager={permissionManager}
                  />
                )}
              </div>
            )}
          </PermissionInfoProvider>
        )}
      </FavoritesProvider>
    </>
  );

  renderDeleteMessage = ({name}) => {
    return (
      <Translate>
        Are you sure you want to delete the location{' '}
        <Param name="name" wrapper={<strong />} value={name} /> and all data associated with it?
      </Translate>
    );
  };

  getInitialEditValues = loc => {
    loc = _.pick(snakifyKeys(loc), [
      'name',
      'room_name_format',
      'map_url_template',
      '_map_url_template_choice',
      'acl_entries',
    ]);
    if (!loc.map_url_template) {
      loc.map_url_template = null;
      loc._map_url_template_choice = 'none';
    } else {
      const template = MAP_TEMPLATE_OPTIONS.find(x => x.value === loc.map_url_template);
      loc._map_url_template_choice = template ? template.value : 'custom';
    }
    return loc;
  };

  render() {
    const {
      isFetching,
      locations,
      canAddItem,
      actions: {createLocation, updateLocation, deleteLocation},
    } = this.props;

    return (
      <EditableList
        title={Translate.string('Locations')}
        addModalTitle={Translate.string('Add location')}
        isFetching={isFetching}
        items={locations}
        initialEditValues={this.getInitialEditValues}
        initialAddValues={{
          room_name_format: '{building}/{floor}-{number}',
          _map_url_template_choice: 'none',
          map_url_template: null,
          acl_entries: [],
        }}
        addFormProps={{decorators: [formDecorator]}}
        editFormProps={{decorators: [formDecorator]}}
        renderItem={this.renderItem}
        canDeleteItem={loc => loc.canDelete}
        canAddItem={canAddItem}
        renderAddForm={this.renderForm}
        renderEditForm={this.renderForm}
        renderDeleteMessage={this.renderDeleteMessage}
        onCreate={createLocation}
        onUpdate={updateLocation}
        onDelete={deleteLocation}
      />
    );
  }
}

export default connect(
  state => ({
    locations: adminSelectors.getAllLocations(state),
    isFetching: adminSelectors.isFetchingLocations(state),
    canAddItem: userSelectors.isUserRBAdmin(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        fetchLocations: adminActions.fetchLocations,
        deleteLocation: ({id}) => adminActions.deleteLocation(id),
        updateLocation: ({id}, data) => adminActions.updateLocation(id, data),
        createLocation: adminActions.createLocation,
      },
      dispatch
    ),
  })
)(LocationPage);
