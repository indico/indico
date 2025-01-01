// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint "react/no-unused-prop-types": "off" */

import PropTypes from 'prop-types';
import React from 'react';

export default class FilterFormComponent extends React.Component {
  static propTypes = {
    setParentField: PropTypes.func.isRequired,
  };

  state = {};

  static getDerivedStateFromProps(props, prevState) {
    // override internal state from props.
    // this allows other widgets and reducers to perform
    // corrections which will be reflected next time the
    // component is rendered
    return {...prevState, ...props};
  }
}
