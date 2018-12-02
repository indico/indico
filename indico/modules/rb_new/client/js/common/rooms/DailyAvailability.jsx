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
import moment from 'moment';
import {Icon} from 'semantic-ui-react';
import TimeRangePicker from '../../components/TimeRangePicker';

import './DailyAvailability.module.scss';

export default class RoomEditModal extends React.Component {
    static propTypes = {
        onChange: PropTypes.func.isRequired,
        onFocus: PropTypes.func.isRequired,
        onBlur: PropTypes.func.isRequired,
        value: PropTypes.arrayOf(PropTypes.object).isRequired,
    };


    render() {
        const {value, onChange, onFocus, onBlur} = this.props;
        if (!value) {
            return;
        }
        return value.map((bookableHour) => {
            return (
                <div key={`${bookableHour.startTime}_${bookableHour.endTime}`} styleName="availability-container">
                    <TimeRangePicker startTime={moment(bookableHour.startTime, 'HH:mm:ss')}
                                     endTime={moment(bookableHour.endTime, 'HH:mm:ss')}
                                     onChange={(startTime, endTime) => onChange([...value, {startTime, endTime}])} />
                    <Icon floated="right" name="trash" styleName="availability-delete-button" />
                </div>
            );
        });
    }
}
