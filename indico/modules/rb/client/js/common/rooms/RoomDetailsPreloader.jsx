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

import {Preloader} from 'indico/react/util';

import * as roomsActions from './actions';
import * as roomsSelectors from './selectors';

const RoomDetailsPreloader = ({roomId, fetchDetails, children}) => (
  <Preloader
    checkCached={state => roomsSelectors.hasDetails(state, {roomId})}
    action={() => fetchDetails(roomId, true)}
    dimmer={
      <Dimmer active page>
        <Loader />
      </Dimmer>
    }
    alwaysLoad
  >
    {children}
  </Preloader>
);

RoomDetailsPreloader.propTypes = {
  roomId: PropTypes.number.isRequired,
  fetchDetails: PropTypes.func.isRequired,
  children: PropTypes.func.isRequired,
};

export default connect(null, dispatch =>
  bindActionCreators(
    {
      fetchDetails: roomsActions.fetchDetails,
    },
    dispatch
  )
)(RoomDetailsPreloader);
