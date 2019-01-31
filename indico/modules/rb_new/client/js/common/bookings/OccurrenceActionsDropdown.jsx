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
import {Button, Confirm, Dropdown} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import * as bookingsActions from './actions';


class OccurrenceActionsDropdown extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        date: PropTypes.string.isRequired,
        actions: PropTypes.exact({
            changeBookingOccurrenceState: PropTypes.func.isRequired,
            fetchBookingDetails: PropTypes.func.isRequired
        }).isRequired,
    };

    state = {
        activeConfirmation: null,
    };

    hideConfirm = () => {
        this.setState({activeConfirmation: null});
    };

    showConfirm = (type) => {
        this.setState({activeConfirmation: type});
    };

    changeOccurrenceState = (date, action, data = {}) => {
        const {booking: {id}, actions: {changeBookingOccurrenceState, fetchBookingDetails}} = this.props;
        changeBookingOccurrenceState(id, date, action, data).then(() => {
            fetchBookingDetails(id);
        });
    };

    render() {
        const {activeConfirmation} = this.state;
        const {date} = this.props;
        return (
            <>
                <Dropdown icon="ellipsis horizontal">
                    <Dropdown.Menu direction="left">
                        <Dropdown.Item icon="times"
                                       text="Cancel occurrence"
                                       onClick={() => this.showConfirm('cancel')} />
                        <Dropdown.Item icon="times" text="Reject occurrence" />
                    </Dropdown.Menu>
                </Dropdown>
                <Confirm header={Translate.string('Confirm cancellation')}
                         content={Translate.string(`Are you sure you want to cancel this occurrence (${date})?`)}
                         confirmButton={<Button content={Translate.string('Cancel occurrence')} negative />}
                         cancelButton={Translate.string('Close')}
                         open={activeConfirmation === 'cancel'}
                         onCancel={this.hideConfirm}
                         onConfirm={() => {
                             this.changeOccurrenceState(date, 'cancel');
                             this.hideConfirm();
                         }} />
            </>
        );
    }
}

export default connect(
    null,
    (dispatch) => ({
        actions: bindActionCreators({
            changeBookingOccurrenceState: bookingsActions.changeBookingOccurrenceState,
            fetchBookingDetails: bookingsActions.fetchBookingDetails
        }, dispatch)
    }),
)(OccurrenceActionsDropdown);
