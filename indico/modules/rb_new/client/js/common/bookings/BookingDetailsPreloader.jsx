/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Dimmer, Loader} from 'semantic-ui-react';

import {Preloader} from 'indico/react/util';
import * as bookingsActions from './actions';
import * as bookingsSelectors from './selectors';


const BookingDetailsPreloader = ({bookingId, component: Component, fetchDetails, onClose}) => (
    <Preloader key={bookingId}
               checkCached={state => bookingsSelectors.hasDetails(state, {bookingId})}
               action={() => fetchDetails(bookingId)}
               dimmer={<Dimmer active page><Loader /></Dimmer>}>
        {() => <Component bookingId={bookingId} onClose={onClose} />}
    </Preloader>
);

BookingDetailsPreloader.propTypes = {
    bookingId: PropTypes.number.isRequired,
    fetchDetails: PropTypes.func.isRequired,
    component: PropTypes.func.isRequired,
    onClose: PropTypes.func.isRequired,
};

export default connect(
    null,
    dispatch => bindActionCreators({
        fetchDetails: bookingsActions.fetchBookingDetails,
    }, dispatch)
)(BookingDetailsPreloader);
