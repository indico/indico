// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Icon, List, Popup} from 'semantic-ui-react';

import {FinalDropdown, FinalInput} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import * as adminActions from './actions';
import EditableList from './EditableList';
import * as adminSelectors from './selectors';

import './EditableList.module.scss';

class EquipmentTypeList extends React.PureComponent {
  static propTypes = {
    isFetching: PropTypes.bool.isRequired,
    equipmentTypes: PropTypes.array.isRequired,
    features: PropTypes.array.isRequired,
    actions: PropTypes.exact({
      deleteEquipmentType: PropTypes.func.isRequired,
      updateEquipmentType: PropTypes.func.isRequired,
      createEquipmentType: PropTypes.func.isRequired,
    }).isRequired,
  };

  renderItem = ({name, features, numRooms}) => (
    <List.Content styleName="info">
      <List.Header>
        <span styleName="name">{name}</span>
        {features.map(feat => (
          <Popup key={feat.name} trigger={<Icon name={feat.icon || 'cog'} color="blue" />}>
            <Translate>
              This equipment type provides the{' '}
              <Param name="name" wrapper={<strong />} value={feat.title} /> feature.
            </Translate>
          </Popup>
        ))}
      </List.Header>
      <List.Description>
        {!numRooms ? (
          <Translate>Currently unused</Translate>
        ) : (
          <PluralTranslate count={numRooms}>
            <Singular>
              Available in{' '}
              <Param name="count" wrapper={<strong />}>
                1
              </Param>{' '}
              room
            </Singular>
            <Plural>
              Available in <Param name="count" wrapper={<strong />} value={numRooms} /> rooms
            </Plural>
          </PluralTranslate>
        )}
      </List.Description>
    </List.Content>
  );

  renderForm = () => {
    const {features} = this.props;

    const featureOptions = features.map(feat => ({
      key: feat.name,
      value: feat.id,
      text: feat.title,
      icon: feat.icon,
    }));

    return (
      <>
        <FinalInput name="name" required label={Translate.string('Name')} autoFocus />
        {featureOptions.length > 0 && (
          <FinalDropdown
            name="features"
            multiple
            selection
            closeOnChange
            options={featureOptions}
            label={Translate.string('Features')}
          />
        )}
      </>
    );
  };

  renderDeleteMessage = ({name, numRooms}) => (
    <>
      <Translate>
        Are you sure you want to delete the equipment type{' '}
        <Param name="name" wrapper={<strong />} value={name} />?
      </Translate>
      {numRooms > 0 && (
        <>
          <br />
          <PluralTranslate count={numRooms}>
            <Singular>
              It is currently used by{' '}
              <Param name="count" wrapper={<strong />}>
                1
              </Param>{' '}
              room.
            </Singular>
            <Plural>
              It is currently used by <Param name="count" wrapper={<strong />} value={numRooms} />{' '}
              rooms.
            </Plural>
          </PluralTranslate>
        </>
      )}
    </>
  );

  render() {
    const {
      isFetching,
      equipmentTypes,
      actions: {createEquipmentType, updateEquipmentType, deleteEquipmentType},
    } = this.props;

    return (
      <EditableList
        title={Translate.string('Equipment types')}
        addModalTitle={Translate.string('Add equipment type')}
        isFetching={isFetching}
        items={equipmentTypes}
        renderItem={this.renderItem}
        renderAddForm={this.renderForm}
        renderEditForm={this.renderForm}
        renderDeleteMessage={this.renderDeleteMessage}
        initialAddValues={{name: '', features: []}}
        initialEditValues={item => ({name: item.name, features: item.features.map(x => x.id)})}
        onCreate={createEquipmentType}
        onUpdate={updateEquipmentType}
        onDelete={deleteEquipmentType}
      />
    );
  }
}

export default connect(
  state => ({
    isFetching: adminSelectors.isFetchingFeaturesOrEquipmentTypes(state),
    equipmentTypes: adminSelectors.getEquipmentTypes(state),
    features: adminSelectors.getFeatures(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        deleteEquipmentType: ({id}) => adminActions.deleteEquipmentType(id),
        updateEquipmentType: ({id}, data) => adminActions.updateEquipmentType(id, data),
        createEquipmentType: adminActions.createEquipmentType,
      },
      dispatch
    ),
  })
)(EquipmentTypeList);
