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

export default class LocationForm extends FilterFormComponent {
  static propTypes = {
    locations: PropTypes.object.isRequired,
    location: PropTypes.number,
    ...FilterFormComponent.propTypes,
  };

  static defaultProps = {
    location: null,
  };

  setLocation = locationId => {
    const {setParentField} = this.props;

    setParentField('locationId', locationId);
  };

  render() {
    const {locations, location} = this.props;
    const options = Array.from(locations, ([id, name]) => ({
      text: name,
      value: id,
    }));

    return (
      <Form.Group>
        <Form.Dropdown
          options={options}
          value={location}
          placeholder={Translate.string('Location')}
          onChange={(__, {value}) => this.setLocation(value || null)}
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
