// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

export default class Filter extends React.Component {
  static propTypes = {
    realms: PropTypes.object.isRequired,
    filters: PropTypes.object.isRequired,
    setFilter: PropTypes.func.isRequired,
  };

  render() {
    const {realms, filters, setFilter} = this.props;
    return (
      <div className="toolbar">
        <div className={`group i-selection ${realms.length <= 1 ? 'hidden' : ''}`}>
          <span className="i-button label">
            <Translate>Show</Translate>
          </span>
          {Object.keys(realms)
            .sort()
            .map(name => (
              <React.Fragment key={name}>
                <input
                  type="checkbox"
                  id={`realm-${name}`}
                  data-realm={name}
                  defaultChecked={filters[name]}
                  onChange={e => setFilter({[name]: e.target.checked})}
                />
                <label htmlFor={`realm-${name}`} className="i-button">
                  {realms[name]}
                </label>
              </React.Fragment>
            ))}
        </div>
      </div>
    );
  }
}
