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
import {Button, Container, Loader, Message} from 'semantic-ui-react';
import DatePicker from 'rc-calendar/lib/Picker';
import Calendar from 'rc-calendar';
import {Translate} from 'indico/react/i18n';
import TimelineContent from './TimelineContent';
import {isDateWithinRange} from '../util';
import TimelineItem from './TimelineItem';
import TimelineLegend from './TimelineLegend';
import {legendLabelShape} from '../props';

import './Timeline.module.scss';


const DATE_FORMAT = 'YYYY-MM-DD';
const _toMoment = (date) => moment(date, DATE_FORMAT);

export default class TimelineBase extends React.Component {
    static propTypes = {
        activeDate: PropTypes.instanceOf(moment).isRequired,
        onDateChange: PropTypes.func.isRequired,
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        legendLabels: PropTypes.arrayOf(legendLabelShape).isRequired,
        emptyMessage: PropTypes.node,
        extraContent: PropTypes.node,
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        step: PropTypes.number,
        onClick: PropTypes.func,
        dateRange: PropTypes.array,
        isLoading: PropTypes.bool,
        recurrenceType: PropTypes.string,
        itemClass: PropTypes.func,
        longLabel: PropTypes.bool,
        disableDatePicker: PropTypes.bool
    };

    static defaultProps = {
        emptyMessage: (
            <Message warning>
                <Translate>
                    No occurrences found
                </Translate>
            </Message>
        ),
        step: 2,
        onClick: null,
        extraContent: null,
        isLoading: false,
        dateRange: [],
        recurrenceType: 'single',
        itemClass: TimelineItem,
        longLabel: false,
        disableDatePicker: false
    };

    calendarDisabledDate = (date) => {
        const {dateRange} = this.props;
        if (!date) {
            return false;
        }
        return dateRange.length !== 0 && !isDateWithinRange(date, dateRange, _toMoment);
    };

    changeSelectedDate = (mode) => {
        const {activeDate, dateRange, onDateChange} = this.props;
        const step = mode === 'next' ? 1 : -1;

        // dateRange is not set (unlimited)
        if (dateRange.length === 0) {
            onDateChange(activeDate.clone().add(step, 'day'));
        } else {
            const index = dateRange.findIndex((dt) => _toMoment(dt).isSame(activeDate)) + step;
            onDateChange(_toMoment(dateRange[index]));
        }
    };

    onSelect = (date) => {
        const {dateRange, onDateChange} = this.props;
        const freeRange = dateRange.length === 0;

        if (freeRange || isDateWithinRange(date, dateRange, _toMoment)) {
            onDateChange(date);
        }
    };

    renderDateSwitcher = () => {
        const {activeDate, dateRange, disableDatePicker, isLoading} = this.props;
        const startDate = _toMoment(dateRange[0]);
        const endDate = _toMoment(dateRange[dateRange.length - 1]);
        const calendar = <Calendar disabledDate={this.calendarDisabledDate} onChange={this.onSelect} />;
        const freeRange = dateRange.length === 0;
        return (
            !disableDatePicker && (
                <Button.Group floated="right" size="small">
                    <Button icon="left arrow"
                            onClick={() => this.changeSelectedDate('prev')}
                            disabled={isLoading || (!freeRange && activeDate.clone().subtract(1, 'day').isBefore(startDate))} />
                    <DatePicker calendar={calendar} disabled={isLoading}>
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
                            disabled={isLoading || activeDate.clone().add(1, 'day').isAfter(endDate)} />
                </Button.Group>
            )
        );
    };

    renderTimeline = () => {
        const {
            extraContent, legendLabels, maxHour, minHour, onClick, recurrenceType, rows, step, isLoading, itemClass,
            longLabel
        } = this.props;
        const hourSeries = _.range(minHour, maxHour + step, step);
        return (
            <>
                <TimelineLegend labels={legendLabels} aside={this.renderDateSwitcher()} />
                <div styleName="timeline">
                    {extraContent}
                    {isLoading ? (
                        <Loader active />
                    ) : (
                        <TimelineContent rows={rows}
                                         hourSeries={hourSeries}
                                         recurrenceType={recurrenceType}
                                         onClick={onClick}
                                         itemClass={itemClass}
                                         longLabel={longLabel} />
                    )}
                </div>
            </>
        );
    };

    renderContent = () => {
        const {emptyMessage, rows, isLoading} = this.props;
        if (!isLoading && _.isEmpty(rows)) {
            return emptyMessage;
        }
        return this.renderTimeline();
    };

    render() {
        return (
            <Container>
                {this.renderContent()}
            </Container>
        );
    }
}
