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
import moment from 'moment';
import PropTypes from 'prop-types';
import shortid from 'shortid';
import {Icon, Button} from 'semantic-ui-react';
import {ANCHOR_RIGHT} from 'react-dates/constants';
import {DateRangePicker} from 'indico/react/components';
import {serializeDate} from 'indico/utils/date';

import './NonBookablePeriods.module.scss';


export default class NonBookablePeriods extends React.Component {
    static propTypes = {
        onChange: PropTypes.func.isRequired,
        value: PropTypes.array.isRequired,
    };

    render() {
        const {onChange, value} = this.props;
        return (
            <>
                <Button type="button"
                        className="room-edit-modal-add-btn"
                        icon labelPosition="left"
                        onClick={() => onChange([...value, {startDt: null, endDt: null, key: shortid.generate()}])}>
                    <Icon name="plus" />
                    Add new Nonbookable Periods
                </Button>
                {value && value.map((dateRangeItem) => {
                    const {startDt, endDt, key} = dateRangeItem;
                    return (
                        <div key={key} className="flex-container">
                            <DateRangePicker small
                                             anchorDirection={ANCHOR_RIGHT}
                                             startDate={startDt === null ? null : moment(startDt)}
                                             endDate={endDt === null ? null : moment(endDt)}
                                             onDatesChange={({startDate, endDate}) => onChange([...value.map(v => (v.key === key ? {...v,
                                                                                                                                    startDt: serializeDate(startDate),
                                                                                                                                    endDt: serializeDate(endDate)} : v))])
                                             } />

                            <Icon floated="right" name="trash" className="trash-button" onClick={() => onChange([...value.filter((dA) => dA.key !== key)])} />
                        </div>
                    );
                })}
                {!value && <div>No non bookable periods found</div>}
            </>

        );
    }
}
