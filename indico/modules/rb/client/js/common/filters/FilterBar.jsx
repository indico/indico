// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import FilterDropdown from './FilterDropdown';

export const FilterBarContext = React.createContext();

export function FilterDropdownFactory({name, ...props}) {
  return (
    <FilterBarContext.Consumer>
      {({state, onDropdownOpen, onDropdownClose}) => (
        <FilterDropdown
          open={state[name]}
          onOpen={() => onDropdownOpen(name)}
          onClose={() => onDropdownClose(name)}
          {...props}
        />
      )}
    </FilterBarContext.Consumer>
  );
}

FilterDropdownFactory.propTypes = {
  name: PropTypes.string.isRequired,
};

export class FilterBarController extends React.Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
  };

  state = {};

  onDropdownOpen = name => {
    this.setState(prevState =>
      Object.assign({}, ...Object.keys(prevState).map(k => ({[k]: null})), {[name]: true})
    );
  };

  onDropdownClose = name => {
    this.setState({
      [name]: false,
    });
  };

  render() {
    const {children} = this.props;
    return (
      <FilterBarContext.Provider
        value={{
          onDropdownOpen: this.onDropdownOpen,
          onDropdownClose: this.onDropdownClose,
          state: this.state,
        }}
      >
        {children}
      </FilterBarContext.Provider>
    );
  }
}
