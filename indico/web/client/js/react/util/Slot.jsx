// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default class Slot extends React.Component {
  static split(children) {
    if (React.Children.toArray(children).every(e => React.isValidElement(e) && e.type === Slot)) {
      const result = {};
      React.Children.forEach(children, child => {
        result[child.props.name] = child.props.children;
      });
      return result;
    } else {
      return {
        content: children,
      };
    }
  }

  static propTypes = {
    // eslint-disable-next-line react/no-unused-prop-types
    name: PropTypes.string,
  };

  static defaultProps = {
    name: 'content',
  };
}
