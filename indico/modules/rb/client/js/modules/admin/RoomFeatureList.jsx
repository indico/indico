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
import {List, Icon} from 'semantic-ui-react';
import {ICONS_AND_ALIASES} from 'semantic-ui-react/dist/commonjs/lib/SUI';

import {formatters, FinalDropdown, FinalInput} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import * as adminActions from './actions';
import EditableList from './EditableList';
import * as adminSelectors from './selectors';

import './EditableList.module.scss';

class RoomFeatureList extends React.PureComponent {
  static propTypes = {
    isFetching: PropTypes.bool.isRequired,
    features: PropTypes.array.isRequired,
    actions: PropTypes.exact({
      deleteFeature: PropTypes.func.isRequired,
      updateFeature: PropTypes.func.isRequired,
      createFeature: PropTypes.func.isRequired,
    }).isRequired,
  };

  renderItem = ({title, icon, numEquipmentTypes}) => (
    <>
      <List.Content>
        <Icon name={icon || 'cog'} size="big" />
      </List.Content>
      <List.Content styleName="info">
        <List.Header>
          <span styleName="name">{title}</span>
        </List.Header>
        <List.Description>
          {!numEquipmentTypes ? (
            <Translate>Currently unused</Translate>
          ) : (
            <PluralTranslate count={numEquipmentTypes}>
              <Singular>
                Provided by{' '}
                <Param name="count" wrapper={<strong />}>
                  1
                </Param>{' '}
                equipment type
              </Singular>
              <Plural>
                Provided by <Param name="count" wrapper={<strong />} value={numEquipmentTypes} />{' '}
                equipment types
              </Plural>
            </PluralTranslate>
          )}
        </List.Description>
      </List.Content>
    </>
  );

  renderForm = () => {
    const iconOptions = ICONS_AND_ALIASES.map(icon => ({
      key: icon,
      value: icon,
      text: icon, // XXX: showing an actual icon here would be nice but then we cannot search
      icon,
    }));

    return (
      <>
        <FinalInput
          name="name"
          required
          format={formatters.slugify}
          formatOnBlur
          label={Translate.string('Name')}
          autoFocus
        />
        <FinalInput name="title" required label={Translate.string('Title')} />
        <FinalDropdown
          name="icon"
          search
          selection
          options={iconOptions}
          label={Translate.string('Icon')}
        />
      </>
    );
  };

  renderDeleteMessage = item => {
    const {title, numEquipmentTypes} = item;

    return (
      <>
        <Translate>
          Are you sure you want to delete the feature{' '}
          <Param name="name" wrapper={<strong />} value={title} />?
        </Translate>
        {numEquipmentTypes > 0 && (
          <>
            <br />
            <PluralTranslate count={numEquipmentTypes}>
              <Singular>
                It is currently provided by{' '}
                <Param name="count" wrapper={<strong />}>
                  1
                </Param>{' '}
                equipment type.
              </Singular>
              <Plural>
                It is currently provided by{' '}
                <Param name="count" wrapper={<strong />} value={numEquipmentTypes} /> equipment
                types.
              </Plural>
            </PluralTranslate>
          </>
        )}
      </>
    );
  };

  render() {
    const {
      isFetching,
      features,
      actions: {createFeature, updateFeature, deleteFeature},
    } = this.props;

    return (
      <EditableList
        title={Translate.string('Features')}
        addModalTitle={Translate.string('Add feature')}
        isFetching={isFetching}
        items={features}
        renderItem={this.renderItem}
        renderAddForm={this.renderForm}
        renderEditForm={this.renderForm}
        renderDeleteMessage={this.renderDeleteMessage}
        onCreate={createFeature}
        onUpdate={updateFeature}
        onDelete={deleteFeature}
      />
    );
  }
}

export default connect(
  state => ({
    isFetching: adminSelectors.isFetchingFeaturesOrEquipmentTypes(state),
    features: adminSelectors.getFeatures(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        deleteFeature: ({id}) => adminActions.deleteFeature(id),
        updateFeature: ({id}, data) => adminActions.updateFeature(id, data),
        createFeature: adminActions.createFeature,
      },
      dispatch
    ),
  })
)(RoomFeatureList);
