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
import * as roomsActions from './actions';
import * as roomsSelectors from './selectors';


const RoomDetailsPreloader = ({roomId, fetchDetails, children}) => (
    <Preloader checkCached={state => roomsSelectors.hasDetails(state, {roomId})}
               action={() => fetchDetails(roomId, true)}
               dimmer={<Dimmer active page><Loader /></Dimmer>}
               alwaysLoad>
        {children}
    </Preloader>
);

RoomDetailsPreloader.propTypes = {
    roomId: PropTypes.number.isRequired,
    fetchDetails: PropTypes.func.isRequired,
    children: PropTypes.func.isRequired,
};

export default connect(
    null,
    dispatch => bindActionCreators({
        fetchDetails: roomsActions.fetchDetails,
    }, dispatch)
)(RoomDetailsPreloader);
