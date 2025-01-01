// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Dimmer, Loader} from 'semantic-ui-react';

import * as blockingsActions from './actions';
import * as blockingsSelectors from './selectors';

class BlockingPreloader extends React.Component {
  static propTypes = {
    blockingId: PropTypes.number.isRequired,
    component: PropTypes.elementType.isRequired,
    componentProps: PropTypes.object,
    blocking: PropTypes.object,
    actions: PropTypes.exact({
      fetchBlocking: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    blocking: undefined,
    componentProps: {},
  };

  componentDidMount() {
    const {
      blocking,
      blockingId,
      actions: {fetchBlocking},
    } = this.props;
    if (!blocking) {
      fetchBlocking(blockingId);
    }
  }

  render() {
    const {blocking, componentProps, component: Component} = this.props;
    if (blocking) {
      return <Component {...componentProps} blocking={blocking} />;
    } else {
      return (
        <Dimmer active page>
          <Loader />
        </Dimmer>
      );
    }
  }
}

export default connect(
  (state, {blockingId}) => ({
    blocking: blockingsSelectors.getBlocking(state, {blockingId}),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        fetchBlocking: blockingsActions.fetchBlocking,
      },
      dispatch
    ),
  }),
  (stateProps, dispatchProps, ownProps) => {
    const {blockingId, component, ...componentProps} = ownProps;
    return {
      blockingId,
      component,
      componentProps,
      ...stateProps,
      ...dispatchProps,
    };
  }
)(BlockingPreloader);
