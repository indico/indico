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
import shortid from 'shortid';
import {Button, Icon} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {serializeTime} from 'indico/utils/date';
import TimeRangePicker from '../../components/TimeRangePicker';

import './DailyAvailability.module.scss';


export default class DailyAvailability extends React.Component {
    static propTypes = {
        onChange: PropTypes.func.isRequired,
        value: PropTypes.arrayOf(PropTypes.object).isRequired,
    };

    handleTimesChange = ({startTime, endTime}, key) => {
        const {value, onChange} = this.props;
        onChange(value.map(v => {
            if (v.key === key) {
                return {...v, startTime: serializeTime(startTime), endTime: serializeTime(endTime)};
            } else {
                return v;
            }
        }));
    };

    render() {
        const {value, onChange} = this.props;
        return (
            <>
                <Button type="button"
                        className="room-edit-modal-add-btn"
                        icon labelPosition="left"
                        onClick={() => onChange([...value, {startTime: '08:00', endTime: '17:00', key: shortid.generate()}])}>
                    <Icon name="plus" />
                    <Translate>Add new Daily Availability</Translate>
                </Button>
                {value && value.map((bookableHour) => {
                    const {startTime: startT, endTime: endT, key} = bookableHour;
                    return (
                        <div key={key} className="flex-container">
                            <TimeRangePicker startTime={moment(startT, 'HH:mm')}
                                             endTime={moment(endT, 'HH:mm')}
                                             onChange={(startTime, endTime) => this.handleTimesChange({startTime, endTime}, key)} />
                            <Icon floated="right" name="trash" className="trash-button" onClick={() => {
                                onChange([...value.filter((bH) => bH.key !== key)]);
                            }} />
                        </div>
                    );
                })}
                {!value && <Translate>No daily availability found</Translate>}
            </>
        );
    }
}
