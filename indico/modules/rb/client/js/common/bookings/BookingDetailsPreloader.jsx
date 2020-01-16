// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Dimmer, Loader} from 'semantic-ui-react';

import {Preloader} from 'indico/react/util';
import * as bookingsActions from './actions';
import * as bookingsSelectors from './selectors';

const BookingDetailsPreloader = ({bookingId, component: Component, fetchDetails, onClose}) => (
  <Preloader
    key={bookingId}
    checkCached={state => bookingsSelectors.hasDetails(state, {bookingId})}
    action={() => fetchDetails(bookingId)}
    dimmer={
      <Dimmer active page>
        <Loader />
      </Dimmer>
    }
    alwaysLoad
  >
    {() => <Component bookingId={bookingId} onClose={onClose} />}
  </Preloader>
);

BookingDetailsPreloader.propTypes = {
  bookingId: PropTypes.number.isRequired,
  fetchDetails: PropTypes.func.isRequired,
  component: PropTypes.elementType.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default connect(
  null,
  dispatch =>
    bindActionCreators(
      {
        fetchDetails: bookingsActions.fetchBookingDetails,
      },
      dispatch
    )
)(BookingDetailsPreloader);
