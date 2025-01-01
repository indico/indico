// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {push} from 'connected-react-router';
import PropTypes from 'prop-types';
import qs from 'qs';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';

import {modalHandlers as bookingsModalHandlers} from '../common/bookings';
import {modalHandlers as roomsModalHandlers} from '../common/rooms';
import {modalHandlers as blockingModalHandlers} from '../modules/blockings';
import {modalHandlers as bookRoomModalHandlers} from '../modules/bookRoom';
import * as globalSelectors from '../selectors';

class ModalController extends React.PureComponent {
  static propTypes = {
    isInitializing: PropTypes.bool.isRequired,
    path: PropTypes.string.isRequired,
    queryString: PropTypes.string.isRequired,
    actions: PropTypes.exact({
      pushState: PropTypes.func.isRequired,
    }).isRequired,
  };

  constructor(props) {
    super(props);

    this.modalHandlers = {
      ...blockingModalHandlers,
      ...bookRoomModalHandlers,
      ...roomsModalHandlers,
      ...bookingsModalHandlers,
    };
  }

  getQueryData() {
    const {queryString} = this.props;
    let {modal: modalData} = qs.parse(queryString);
    if (!modalData) {
      return null;
    }
    if (Array.isArray(modalData)) {
      modalData = modalData[modalData.length - 1];
    }
    const match = modalData.match(/^([^:]+)(?::(\d+)(?::(.+))?)?$/); // foo[:123[:...]]
    if (!match) {
      return null;
    }
    const [orig, name, value, payload] = match;
    return {orig, name, value: parseInt(value, 10), payload: JSON.parse(payload || 'null')};
  }

  getQueryStringWithout(arg) {
    const {queryString} = this.props;
    const params = qs.parse(queryString);
    if (Array.isArray(params.modal)) {
      params.modal = params.modal.filter(x => x !== arg);
    } else if (params.modal === arg) {
      delete params.modal;
    }
    return qs.stringify(params, {arrayFormat: 'repeat'});
  }

  getQueryStringWithoutModals() {
    const {queryString} = this.props;
    const params = qs.parse(queryString);
    delete params.modal;
    return qs.stringify(params, {arrayFormat: 'repeat'});
  }

  makeCloseHandler(qsArg) {
    const {
      actions: {pushState},
      path,
    } = this.props;
    return closeAll => {
      const queryString = closeAll
        ? this.getQueryStringWithoutModals()
        : this.getQueryStringWithout(qsArg);
      pushState(path + (queryString ? `?${queryString}` : ''));
    };
  }

  render() {
    const {isInitializing} = this.props;
    if (isInitializing) {
      return null;
    }
    const queryData = this.getQueryData();
    if (!queryData) {
      return null;
    }
    const {orig, name, value, payload} = queryData;
    const closeHandler = this.makeCloseHandler(orig);
    const handler = this.modalHandlers[name];
    return handler ? handler(closeHandler, value, payload) : null;
  }
}

export default connect(
  state => ({
    isInitializing: globalSelectors.isInitializing(state),
    path: state.router.location.pathname,
    queryString: state.router.location.search.substr(1),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        pushState: push,
      },
      dispatch
    ),
  })
)(ModalController);
