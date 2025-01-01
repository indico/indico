// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {FilterFormComponent} from '../../../common/filters';

export default class BuildingForm extends FilterFormComponent {
  static propTypes = {
    buildings: PropTypes.array.isRequired,
    building: PropTypes.string,
    ...FilterFormComponent.propTypes,
  };

  static defaultProps = {
    building: null,
  };

  constructor(props) {
    super(props);

    const {building} = this.props;
    this.state = {building};
  }

  setBuilding = building => {
    const {setParentField} = this.props;

    this.setState({building}, () => {
      setParentField('building', building);
    });
  };

  render() {
    const {buildings} = this.props;
    const {building} = this.state;
    const options = buildings.map(buildingNumber => ({
      text: Translate.string('Building {buildingNumber}', {buildingNumber}),
      value: buildingNumber,
    }));

    return (
      <Form.Group>
        <Form.Dropdown
          options={options}
          value={building}
          placeholder={Translate.string('Building')}
          onChange={(__, {value}) => this.setBuilding(value || null)}
          closeOnChange
          closeOnBlur
          search
          selection
          clearable
        />
      </Form.Group>
    );
  }
}
