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
import {SingleDatePicker} from 'indico/react/components';
import TimeRangePicker from '../../components/TimeRangePicker';

import './NonBookablePeriods.module.scss';


export default class NonBookablePeriods extends React.Component {
    static propTypes = {
        onChange: PropTypes.func.isRequired,
        onFocus: PropTypes.func.isRequired,
        onBlur: PropTypes.func.isRequired,
        value: PropTypes.array.isRequired,
        disabled: PropTypes.bool,
    };

    static defaultProps = {
        disabled: false,
    };

    render() {
        const {onChange, onFocus, onBlur, value} = this.props;
        return (
            <>
                {value.map((dateRangeItem) => {
                    const {startDt, endDt} = dateRangeItem;
                    return (
                        <>
                            <div styleName="periods-container">
                                <SingleDatePicker key={`${startDt}_${endDt}`}
                                                  date={moment(startDt)}
                                                  DatesChange={({startDate}) => null} />
                                <SingleDatePicker key={`${startDt}_${endDt}`}
                                                  date={moment(endDt)}
                                                  DatesChange={({startDate}) => null} />
                            </div>
                            <TimeRangePicker startTime={moment(startDt)}
                                             endTime={moment(endDt)}
                                             onChange={(startTime, endTime) => null} />
                        </>
                    );
                })}
            </>

        );
    }
}
