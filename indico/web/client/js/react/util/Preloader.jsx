// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';

class Preloader extends React.Component {
  static propTypes = {
    isCached: PropTypes.bool.isRequired,
    alwaysLoad: PropTypes.bool,
    action: PropTypes.func.isRequired,
    children: PropTypes.func.isRequired,
    dimmer: PropTypes.element.isRequired,
  };

  static defaultProps = {
    alwaysLoad: false,
  };

  componentDidMount() {
    const {action, isCached, alwaysLoad} = this.props;
    if (!isCached || alwaysLoad) {
      action();
    }
  }

  render() {
    const {children, dimmer, isCached} = this.props;
    return isCached ? children() : dimmer;
  }
}

export default connect((state, {checkCached}) => ({
  isCached: checkCached(state),
}))(Preloader);
