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
import {Button, Icon, Segment} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';
import {toMoment} from 'indico/utils/date';
import {renderRecurrence} from '../util';

import './TimeInformation.module.scss';


function TimeInformation({recurrence, dates: {startDate, endDate}, timeSlot, onClickOccurrences,
                          occurrenceCount}) {
    const mStartDate = toMoment(startDate);
    const mEndDate = endDate ? toMoment(endDate) : null;
    let timeInfo = null;

    if (timeSlot) {
        const {startTime, endTime} = timeSlot;
        const mStartTime = toMoment(startTime, 'HH:mm');
        const mEndTime = endTime ? toMoment(endTime, 'HH:mm') : null;
        timeInfo = (
            <Segment>
                <Icon name="clock" />
                <strong>{mStartTime.format('LT')}</strong>
                {' → '}
                <strong>{mEndTime.format('LT')}</strong>
            </Segment>
        );
    }
    return (
        <div styleName="booking-time-info">
            <Segment.Group>
                <Segment color="teal">
                    <div>
                        <Icon name="calendar outline" />
                        {(mEndDate && !mStartDate.isSame(mEndDate, 'day'))
                            ? (
                                <Translate>
                                    <Param name="startDate" wrapper={<strong />} value={mStartDate.format('L')} /> to
                                    {' '}
                                    <Param name="endDate" wrapper={<strong />} value={mEndDate.format('L')} />
                                </Translate>
                            ) : (
                                <strong>{mStartDate.format('L')}</strong>
                            )
                        }
                    </div>
                </Segment>
                {timeInfo}
                <Segment>
                    <div styleName="occurrences-details">
                        <div>
                            <Icon name="list" />
                            <strong>
                                {renderRecurrence(recurrence)}
                                {(occurrenceCount > 1) && (
                                    <>
                                        {', '}
                                        <Translate>
                                            <Param name="count" value={occurrenceCount} /> occurrences
                                        </Translate>
                                    </>
                                )}
                            </strong>
                        </div>
                        <Button size="small" basic color="teal" onClick={onClickOccurrences}>
                            <Translate>See on timeline</Translate>
                        </Button>
                    </div>
                </Segment>
            </Segment.Group>
        </div>
    );
}

TimeInformation.propTypes = {
    recurrence: PropTypes.object.isRequired,
    dates: PropTypes.shape({
        startDate: PropTypes.string.isRequired,
        endDate: PropTypes.string
    }).isRequired,
    timeSlot: PropTypes.shape({
        startTime: PropTypes.string,
        endTime: PropTypes.string
    }),
    onClickOccurrences: PropTypes.func.isRequired,
    occurrenceCount: PropTypes.number
};

TimeInformation.defaultProps = {
    timeSlot: null,
    occurrenceCount: 0
};

export default Overridable.component('TimeInformation', TimeInformation);
