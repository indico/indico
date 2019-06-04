// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Icon, Input} from 'semantic-ui-react';

import {FilterFormComponent} from '../../../common/filters';

import './CapacityForm.module.scss';

export default class CapacityForm extends FilterFormComponent {
  setCapacity(capacity) {
    const {setParentField} = this.props;

    setParentField('capacity', capacity);
    this.setState({
      capacity,
    });
  }

  render() {
    const {capacity} = this.state;
    const icon = <Icon name="close" onClick={() => this.setCapacity(null)} link />;
    return (
      <div styleName="capacity-form">
        <Input
          type="number"
          min="1"
          step="1"
          icon={capacity ? icon : null}
          value={capacity || ''}
          onChange={(__, {value}) => {
            this.setCapacity(!value ? null : Math.abs(+value));
          }}
        />
      </div>
    );
  }
}
