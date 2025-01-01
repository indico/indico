// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default class MessageBox extends React.Component {
  static propTypes = {
    type: PropTypes.oneOf(['info', 'highlight', 'error', 'danger', 'warning', 'success'])
      .isRequired,
    icon: PropTypes.bool,
    fixedWidth: PropTypes.bool,
    largeIcon: PropTypes.bool,
    children: PropTypes.any.isRequired,
  };

  static defaultProps = {
    icon: true,
    fixedWidth: false,
    largeIcon: false,
  };

  render() {
    const {type, icon, fixedWidth, largeIcon, children} = this.props;
    return (
      <div
        className={`${type}-message-box ${fixedWidth ? 'fixed-width' : ''} ${
          largeIcon ? 'large-icon' : ''
        }`}
      >
        <div className="message-box-content">
          {icon && <span className="icon" />}
          <div className="message-text">{children}</div>
        </div>
      </div>
    );
  }
}
