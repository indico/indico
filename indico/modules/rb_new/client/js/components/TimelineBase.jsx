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
import React from 'react';
import PropTypes from 'prop-types';
import {Button, Container, Label, Loader, Message, Segment} from 'semantic-ui-react';
import DatePicker from 'rc-calendar/lib/Picker';
import Calendar from 'rc-calendar';
import {Translate} from 'indico/react/i18n';
import TimelineContent from './TimelineContent';
import {isDateWithinRange} from '../util';

import './Timeline.module.scss';


const DATE_FORMAT = 'YYYY-MM-DD';
const _toMoment = (date) => moment(date, DATE_FORMAT);

export default class TimelineBase extends React.Component {
    static propTypes = {
        activeDate: PropTypes.instanceOf(moment),
        onDateChange: PropTypes.func.isRequired,
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        legend: PropTypes.node.isRequired,
        emptyMessage: PropTypes.node,
        extraContent: PropTypes.node,
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        step: PropTypes.number,
        onClick: PropTypes.func,
        dateRange: PropTypes.array.isRequired,
        isFetching: PropTypes.bool.isRequired,
        isFetchingRooms: PropTypes.bool.isRequired,
        recurrenceType: PropTypes.string.isRequired,
    };

    static defaultProps = {
        emptyMessage: (
            <Message warning>
                <Translate>
                    There are no rooms matching the criteria.
                </Translate>
            </Message>
        ),
        step: 2,
        onClick: null,
        activeDate: null,
        extraContent: null
    };

    calendarDisabledDate = (date) => {
        const {dateRange} = this.props;
        if (!date) {
            return false;
        }
        return !isDateWithinRange(date, dateRange, _toMoment);
    };

    changeSelectedDate = (mode) => {
        const {activeDate, dateRange, onDateChange} = this.props;
        const index = dateRange.findIndex((dt) => _toMoment(dt).isSame(activeDate)) + (mode === 'next' ? 1 : -1);
        onDateChange(_toMoment(dateRange[index]));
    };

    onSelect = (date) => {
        const {dateRange, onDateChange} = this.props;
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);

        if (date.isBefore(_toMoment(startDate)) || date.isAfter(_toMoment(endDate))) {
            return;
        } else if (isDateWithinRange(date, dateRange, _toMoment)) {
            onDateChange(date);
        }
    };

    renderTimeline = () => {
        const {
            activeDate, dateRange, extraContent, legend, maxHour, minHour, onClick, recurrenceType, rows, step
        } = this.props;
        const hourSeries = _.range(minHour, maxHour + step, step);
        const calendar = <Calendar disabledDate={this.calendarDisabledDate} onChange={this.onSelect} />;
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);

        return (
            <>
                <Segment styleName="legend" basic>
                    <Label.Group as="span" size="large" styleName="labels">
                        {legend}
                    </Label.Group>
                    {rows.length > 1 && (
                        <Button.Group floated="right" size="small">
                            <Button icon="left arrow"
                                    onClick={() => this.changeSelectedDate('prev')}
                                    disabled={activeDate.clone().subtract(1, 'day').isBefore(startDate)} />
                            <DatePicker calendar={calendar}>
                                {
                                    () => (
                                        <Button primary>
                                            {activeDate.format(DATE_FORMAT)}
                                        </Button>
                                    )
                                }
                            </DatePicker>
                            <Button icon="right arrow"
                                    onClick={() => this.changeSelectedDate('next')}
                                    disabled={activeDate.clone().add(1, 'day').isAfter(endDate)} />
                        </Button.Group>
                    )}
                </Segment>
                <div styleName="timeline">
                    {extraContent}
                    <TimelineContent rows={rows}
                                     hourSeries={hourSeries}
                                     recurrenceType={recurrenceType}
                                     onClick={onClick} />
                </div>
            </>
        );
    };

    renderContent = () => {
        const {isFetching, isFetchingRooms, emptyMessage, rows} = this.props;
        if (isFetching || isFetchingRooms) {
            return <Loader active />;
        } else if (!_.isEmpty(rows)) {
            return this.renderTimeline();
        } else {
            return emptyMessage;
        }
    };

    render() {
        return (
            <Container>
                {this.renderContent()}
            </Container>
        );
    }
}
