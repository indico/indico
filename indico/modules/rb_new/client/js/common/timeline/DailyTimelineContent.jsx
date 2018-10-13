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
import {Icon, Loader, Popup} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';
import {Translate} from 'indico/react/i18n';
import {TooltipIfTruncated} from 'indico/react/components';

import TimelineItem from './TimelineItem';

import './TimelineContent.module.scss';


export default class DailyTimelineContent extends React.Component {
    static propTypes = {
        step: PropTypes.number,
        rows: PropTypes.array.isRequired,
        onClickCandidate: PropTypes.func,
        onClickReservation: PropTypes.func,
        longLabel: PropTypes.bool,
        onClickLabel: PropTypes.func,
        itemClass: PropTypes.func,
        itemProps: PropTypes.object,
        isLoading: PropTypes.bool,
        lazyScroll: PropTypes.object,
        minHour: PropTypes.number,
        maxHour: PropTypes.number,
        hourStep: PropTypes.number,
        showUnused: PropTypes.bool,
    };

    static defaultProps = {
        step: 2,
        onClickCandidate: null,
        onClickReservation: null,
        longLabel: false,
        onClickLabel: null,
        itemClass: TimelineItem,
        itemProps: {},
        isLoading: false,
        lazyScroll: null,
        minHour: 6,
        maxHour: 22,
        hourStep: 2,
        showUnused: true
    };

    state = {
        selectable: true
    };

    onClickLabel = (id) => {
        const {onClickLabel} = this.props;
        return onClickLabel ? () => onClickLabel(id) : false;
    };

    hasUsage = (availability) => {
        const fields = ['preBookings', 'blockings', 'bookings', 'nonbookablePeriods', 'unbookableHours', 'candidates'];
        return fields.some(field => !_.isEmpty(availability[field]));
    };

    renderTimelineRow({availability, label, conflictIndicator, key, room}) {
        const {
            minHour, maxHour, hourStep, itemClass: ItemClass, itemProps, onClickCandidate,
            onClickReservation, longLabel, showUnused
        } = this.props;
        const columns = ((maxHour - minHour) / hourStep) + 1;
        const hasConflicts = !(_.isEmpty(availability.conflicts) && _.isEmpty(availability.preConflicts));
        if (!showUnused && !this.hasUsage(availability)) {
            return null;
        }

        return (
            <div styleName="timeline-row" key={`element-${key}`}>
                <TimelineRowLabel label={label}
                                  availability={conflictIndicator ? (hasConflicts ? 'conflict' : 'available') : null}
                                  longLabel={longLabel}
                                  onClickLabel={this.onClickLabel(room.id)} />
                <div styleName="timeline-row-content" style={{flex: columns}}>
                    <ItemClass startHour={minHour} endHour={maxHour} data={availability} room={room}
                               onClickReservation={onClickReservation}
                               onClickCandidate={() => {
                                   if (onClickCandidate && !hasConflicts) {
                                       onClickCandidate(room.id);
                                   }
                               }}
                               setSelectable={selectable => {
                                   this.setState({selectable});
                               }}
                               {...itemProps} />
                </div>
            </div>
        );
    }

    renderDividers(count, step) {
        const leftOffset = (100 / count);

        return _.range(0, count, step).map(i => (
            // eslint-disable-next-line react/no-array-index-key
            <div styleName="timeline-divider"
                 style={{left: `${(i * leftOffset)}%`}}
                 key={`divider-${i}`} />
        ));
    }

    renderHeader(hourSpan, hourSeries) {
        const {selectable} = this.state;
        const {longLabel, hourStep} = this.props;
        const labelWidth = longLabel ? 200 : 150;

        return (
            <div styleName="timeline-header" className={!selectable && 'timeline-non-selectable'}>
                <div style={{width: labelWidth}} />
                <div styleName="timeline-header-labels">
                    {_.range(0, hourSpan, hourStep).map((i, n) => (
                        <div styleName="timeline-header-label"
                             key={`timeline-header-${i}`}
                             style={{position: 'absolute', left: `${i / hourSpan * 100}%`}}>
                            <span styleName="timeline-label-text">
                                {moment({hours: hourSeries[n]}).format('LT')}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    render() {
        const {rows, minHour, maxHour, hourStep, longLabel, lazyScroll, isLoading} = this.props;
        const {selectable} = this.state;
        const labelWidth = longLabel ? 200 : 150;
        const WrapperComponent = lazyScroll ? LazyScroll : React.Fragment;
        const wrapperProps = lazyScroll || {};
        const hourSeries = _.range(minHour, maxHour + hourStep, hourStep);
        const hourSpan = maxHour - minHour;

        return (
            <>
                {!!rows.length && this.renderHeader(hourSpan, hourSeries)}
                <WrapperComponent {...wrapperProps}>
                    <div styleName="timeline-content" className={!selectable && 'timeline-non-selectable'}>
                        {rows.map((rowProps) => this.renderTimelineRow(rowProps))}
                        <div style={{left: labelWidth, width: `calc(100% - ${labelWidth}px)`}}
                             styleName="timeline-lines">
                            {this.renderDividers(hourSpan, hourStep)}
                        </div>
                    </div>
                    <Loader active={wrapperProps.isFetching || isLoading} inline="centered" styleName="timeline-loader" />
                </WrapperComponent>
            </>
        );
    }
}

export function TimelineRowLabel({label, availability, longLabel, onClickLabel}) {
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
            {availability && <Icon name="circle" size="tiny" color={color} styleName="dot" />}
            {onClickLabel ? <a onClick={onClickLabel}>{label}</a> : <span>{label}</span>}
        </span>
    );
    const width = longLabel ? 200 : 150;

    return (
        <TooltipIfTruncated>
            <div styleName="timeline-row-label" style={{
                minWidth: width,
                maxWidth: width
            }}>
                <div styleName="label">
                    {availability ? <Popup trigger={roomLabel} content={tooltip} size="small" /> : roomLabel}
                </div>
            </div>
        </TooltipIfTruncated>
    );
}

TimelineRowLabel.propTypes = {
    label: PropTypes.string.isRequired,
    availability: PropTypes.oneOf(['available', 'alternatives', 'conflict']),
    longLabel: PropTypes.bool,
    onClickLabel: PropTypes.oneOfType([
        PropTypes.func,
        PropTypes.bool
    ])
};

TimelineRowLabel.defaultProps = {
    availability: null,
    longLabel: false,
    onClickLabel: null,
};
