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
import {Icon, Segment, Label} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';
import recurrenceRenderer from './RecurrenceRenderer';

import './BookingTimeInformation.module.scss';


export default function BookingTimeInformation({recurrence, dates, timeSlot}) {
    const {startDate, endDate} = dates;
    const {startTime, endTime} = timeSlot;
    const {type} = recurrence;
    const sDate = toMoment(startDate);
    const eDate = endDate ? toMoment(endDate) : null;
    const sTime = toMoment(startTime, 'HH:mm');
    const eTime = endTime ? toMoment(endTime, 'HH:mm') : null;

    return (
        <div styleName="booking-time-info">
            <Segment attached="top" color="teal">
                <Icon name="calendar outline" />
                {(endDate && startDate !== endDate)
                    ? (
                        <Translate>
                            <Param name="startTime"
                                   wrapper={<strong />}
                                   value={sDate.format('L')} /> to <Param name="endTime"
                                                                          wrapper={<strong />}
                                                                          value={eDate.format('L')} />
                        </Translate>
                    ) : (
                        <strong>{sDate.format('L')}</strong>
                    )
                }
                {(type === 'daily' || type === 'every') && (
                    <Label basic pointing="left">
                        {recurrenceRenderer(recurrence)}
                    </Label>
                )}
            </Segment>
            <Segment attached="bottom">
                <Icon name="clock" />
                <strong>{sTime.format('LT')}</strong>
                {' '}&rarr;{' '}
                <strong>{eTime.format('LT')}</strong>
            </Segment>
        </div>
    );
}

BookingTimeInformation.propTypes = {
    recurrence: PropTypes.object.isRequired,
    dates: PropTypes.object.isRequired,
    timeSlot: PropTypes.object.isRequired
};
