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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Loader, Statistic} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';

import * as landingActions from './actions';
import * as landingSelectors from './selectors';


const defaultLabels = {
    activeRooms: <Translate>Active rooms</Translate>,
    buildings: <Translate>Buildings</Translate>,
    bookingsToday: <Translate>Bookings today</Translate>,
    pendingBookings: <Translate>Active booking requests</Translate>
};

class LandingStatistics extends React.Component {
    static propTypes = {
        hasStatistics: PropTypes.bool.isRequired,
        statistics: PropTypes.shape({
            activeRooms: PropTypes.number.isRequired,
            bookingsToday: PropTypes.number.isRequired,
            buildings: PropTypes.number.isRequired,
            pendingBookings: PropTypes.number.isRequired,
        }),
        actions: PropTypes.exact({
            fetchStatistics: PropTypes.func.isRequired,
        }).isRequired,
        labels: PropTypes.object
    };

    static defaultProps = {
        statistics: null,
        labels: {}
    };

    componentDidMount() {
        const {actions: {fetchStatistics}} = this.props;
        fetchStatistics();
    }

    render() {
        const {hasStatistics} = this.props;
        if (!hasStatistics) {
            return <Loader size="massive" active />;
        }
        const {statistics: {activeRooms, bookingsToday, buildings, pendingBookings}, labels} = this.props;
        const finalLabels = {...defaultLabels, ...labels};
        return (
            <div className="statistics">
                <Statistic size="huge">
                    <Statistic.Value>
                        {activeRooms}
                    </Statistic.Value>
                    <Statistic.Label>
                        {finalLabels.activeRooms}
                    </Statistic.Label>
                </Statistic>
                <Statistic size="huge">
                    <Statistic.Value>
                        {buildings}
                    </Statistic.Value>
                    <Statistic.Label>
                        {finalLabels.buildings}
                    </Statistic.Label>
                </Statistic>
                <Statistic size="huge">
                    <Statistic.Value>
                        {bookingsToday}
                    </Statistic.Value>
                    <Statistic.Label>
                        {finalLabels.bookingsToday}
                    </Statistic.Label>
                </Statistic>
                <Statistic size="huge">
                    <Statistic.Value>
                        {pendingBookings}
                    </Statistic.Value>
                    <Statistic.Label>
                        {finalLabels.pendingBookings}
                    </Statistic.Label>
                </Statistic>
            </div>
        );
    }
}

export default connect(
    state => ({
        statistics: landingSelectors.getStatistics(state),
        hasStatistics: landingSelectors.hasStatistics(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchStatistics: landingActions.fetchStatistics,
        }, dispatch)
    })
)(Overridable.component('LandingStatistics', LandingStatistics));
