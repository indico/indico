// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import _ from 'lodash';
import {Dropdown, Icon, List} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import * as roomsSelectors from '../selectors';

import './EquipmentList.module.scss';

class EquipmentList extends React.Component {
  static propTypes = {
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
    value: PropTypes.array.isRequired,
    label: PropTypes.string.isRequired,
    equipmentTypes: PropTypes.arrayOf(PropTypes.object).isRequired,
  };

  get generateEquipmentOptions() {
    const {value, equipmentTypes} = this.props;
    return equipmentTypes
      .filter(eq => !value.includes(eq.id))
      .map(eq => ({key: eq.id, text: eq.name, value: eq.id}));
  }

  render() {
    const {onChange, onFocus, onBlur, value, equipmentTypes, label} = this.props;
    const equipmentTypesMap = _.mapKeys(equipmentTypes, 'id');
    const options = this.generateEquipmentOptions;
    return (
      <>
        <Dropdown
          button
          text={label}
          className="icon"
          floating
          labeled
          icon="add"
          options={options}
          search
          onFocus={onFocus}
          onBlur={onBlur}
          disabled={options.length === 0}
          selectOnBlur={false}
          value={null}
          onChange={(event, values) => {
            onChange([...value, values.value]);
          }}
        />
        <List key="equipment" divided>
          {value &&
            value.map(equipmentId => (
              <List.Item key={equipmentId}>
                <List.Content floated="right">
                  <Icon
                    styleName="equipment-button"
                    name="remove"
                    onClick={() => {
                      onChange(value.filter(x => x !== equipmentId));
                    }}
                  />
                </List.Content>
                <List.Content>{equipmentTypesMap[equipmentId].name}</List.Content>
              </List.Item>
            ))}
        </List>
        {value.length === 0 && (
          <div>
            <Translate>No equipment found</Translate>
          </div>
        )}
      </>
    );
  }
}

export default connect(state => ({
  equipmentTypes: roomsSelectors.getAllEquipmentTypes(state),
}))(EquipmentList);
