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

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Button, Container, Label, Loader, Message, Segment, Icon, Popup} from 'semantic-ui-react';
import DatePicker from 'rc-calendar/lib/Picker';
import Calendar from 'rc-calendar';
import {Translate} from 'indico/react/i18n';
import {TooltipIfTruncated} from 'indico/react/components';
import TimelineItem from './TimelineItem';
import BookRoomModal from '../containers/BookRoomModal';

import './Timeline.module.scss';


const DATE_FORMAT = 'YYYY-MM-DD';
const _toMoment = (date) => moment(date, DATE_FORMAT);


export default class Timeline extends React.Component {
    static propTypes = {
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        step: PropTypes.number,
        dateRange: PropTypes.array.isRequired,
        availability: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        resetBookingState: PropTypes.func.isRequired,
        recurrenceType: PropTypes.string.isRequired
    };

    static defaultProps = {
        step: 2
    };

    constructor(props) {
        super(props);

        const {dateRange} = this.props;
        this.state = {
            activeDate: _toMoment(dateRange[0])
        };
    }

    changeSelectedDate = (mode) => {
        const {dateRange} = this.props;
        const {activeDate} = this.state;
        const index = dateRange.findIndex((dt) => _toMoment(dt).isSame(activeDate)) + (mode === 'next' ? 1 : -1);

        this.setState({activeDate: _toMoment(dateRange[index])});
    };

    isDateWithinTimelineRange = (date) => {
        const {dateRange} = this.props;
        return dateRange.filter((dt) => _toMoment(dt).isSame(date, 'day')).length !== 0;
    };

    onSelect = (date) => {
        const {dateRange} = this.props;
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);

        if (date.isBefore(_toMoment(startDate)) || date.isAfter(_toMoment(endDate))) {
            return;
        } else if (this.isDateWithinTimelineRange(date)) {
            this.setState({activeDate: date});
        }
    };

    renderContent = () => {
        const {isFetching, availability} = this.props;
        if (isFetching) {
            return <Loader size="massive" active />;
        } else if (!_.isEmpty(availability)) {
            return this.renderTimeline();
        } else {
            return this.renderEmptyMessage();
        }
    };

    calendarDisabledDate = (date) => {
        if (!date) {
            return false;
        }
        return !this.isDateWithinTimelineRange(date);
    };

    renderTimeline = () => {
        const {activeDate} = this.state;
        const {minHour, maxHour, step, availability, dateRange} = this.props;
        const hourSeries = _.range(minHour, maxHour + step, step);
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);

        let currentDate = activeDate;
        if (!this.isDateWithinTimelineRange(currentDate)) {
            currentDate = _toMoment(startDate);
            this.setState({activeDate: currentDate});
        }

        const calendar = <Calendar disabledDate={this.calendarDisabledDate} onChange={this.onSelect} />;
        return (
            <>
                <Segment styleName="legend" basic>
                    <Label.Group as="span" size="large" styleName="labels">
                        <Label color="green">{Translate.string('Available')}</Label>
                        <Label color="orange">{Translate.string('Booked')}</Label>
                        <Label styleName="pre-booking">{Translate.string('Pre-Booking')}</Label>
                        <Label color="red">{Translate.string('Conflict')}</Label>
                        <Label styleName="pre-booking-conflict">{Translate.string('Conflict with Pre-Booking')}</Label>
                    </Label.Group>
                    <Button.Group floated="right" size="small">
                        <Button icon="left arrow"
                                onClick={() => this.changeSelectedDate('prev')}
                                disabled={moment(currentDate).subtract(1, 'day').isBefore(startDate)} />
                        <DatePicker calendar={calendar}>
                            {
                                () => (
                                    <Button primary>
                                        {currentDate.format(DATE_FORMAT)}
                                    </Button>
                                )
                            }
                        </DatePicker>
                        <Button icon="right arrow"
                                onClick={() => this.changeSelectedDate('next')}
                                disabled={moment(currentDate).add(1, 'day').isAfter(endDate)} />
                    </Button.Group>
                </Segment>
                <div styleName="timeline">
                    <div styleName="timeline-header">
                        <div styleName="timeline-header-label" />
                        {hourSeries.map((hour) => (
                            <div styleName="timeline-header-label" key={`timeline-header-${hour}`}>
                                {moment({hours: hour}).format('H:mm')}
                            </div>
                        ))}
                    </div>
                    {Object.entries(availability).map(([, roomAvailability]) => (
                        this.renderTimelineRow(roomAvailability)
                    ))}
                    {this.renderDividers(hourSeries.length)}
                </div>
            </>
        );
    };

    renderTimelineRow = (availability) => {
        const {activeDate} = this.state;
        const {minHour, maxHour, step, recurrenceType} = this.props;
        const columns = ((maxHour - minHour) / step) + 1;
        const data = {
            candidates: availability.candidates[activeDate.format('YYYY-MM-DD')] || [],
            preBookings: availability.pre_bookings[activeDate.format('YYYY-MM-DD')] || [],
            bookings: availability.bookings[activeDate.format('YYYY-MM-DD')] || [],
            conflicts: availability.conflicts[activeDate.format('YYYY-MM-DD')] || [],
            preConflicts: availability.pre_conflicts[activeDate.format('YYYY-MM-DD')] || []
        };
        // TODO: Consider plan B (availability='alternatives') option when implemented
        const hasConflicts = !(_.isEmpty(availability.conflicts) && _.isEmpty(availability.pre_conflicts));
        return (
            <div styleName="timeline-row" key={`room-${availability.room.id}`}>
                <TimelineRowLabel roomName={availability.room.full_name}
                                  availability={hasConflicts ? 'conflict' : 'available'} />
                <div styleName="timeline-row-content" style={{flex: columns}}>
                    <TimelineItem step={step} startHour={minHour} endHour={maxHour} data={data}
                                  bookable={!hasConflicts}
                                  onClick={() => {
                                      if (!hasConflicts || recurrenceType !== 'single') {
                                          this.openBookingModal(availability.room);
                                      }
                                  }} />
                </div>
            </div>
        );
    };

    renderDividers = (count) => {
        const leftOffset = 100 / (count + 1);

        return (
            _.times(count, (i) => (
                // eslint-disable-next-line react/no-array-index-key
                <div styleName="divider" style={{left: `${(i + 1) * leftOffset}%`}} key={`divider-${i}`} />
            ))
        );
    };

    renderEmptyMessage = () => {
        return (
            <Message warning>
                <Translate>
                    There are no rooms matching the criteria.
                </Translate>
            </Message>
        );
    };

    openBookingModal = (room) => {
        this.setState({
            bookingModal: true,
            selectedRoom: room
        });
    };

    closeBookingModal = () => {
        const {resetBookingState} = this.props;
        resetBookingState();
        this.setState({
            bookingModal: false
        });
    };

    render() {
        const {bookingModal, selectedRoom} = this.state;
        return (
            <Container>
                {this.renderContent()}
                <BookRoomModal open={bookingModal}
                               room={selectedRoom}
                               onClose={this.closeBookingModal} />
            </Container>
        );
    }
}

function TimelineRowLabel({roomName, availability}) {
    let color, tooltip;
    switch (availability) {
        case 'conflict':
            color = 'red';
            tooltip = Translate.string('Conflicts for the selected period');
            break;
        case 'alternatives':
            color = 'orange';
            tooltip = Translate.string('Room suggested based on the selected criteria');
            break;
        default:
            color = 'green';
            tooltip = Translate.string('Room available');
    }
    const roomLabel = (
        <span>
            <Icon name="circle" size="tiny" color={color} styleName="dot" />
            <span>{roomName}</span>
        </span>
    );

    return (
        <TooltipIfTruncated>
            <div styleName="timeline-row-label">
                <div styleName="label">
                    <Popup trigger={roomLabel} content={tooltip} size="small" />
                </div>
            </div>
        </TooltipIfTruncated>
    );
}

TimelineRowLabel.propTypes = {
    roomName: PropTypes.string.isRequired,
    availability: PropTypes.oneOf(['available', 'alternatives', 'conflict']).isRequired
};
