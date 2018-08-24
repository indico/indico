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
import {Icon, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {TooltipIfTruncated} from 'indico/react/components';

import TimelineItem from './TimelineItem';

import './TimelineContent.module.scss';


export default class TimelineContent extends React.Component {
    static propTypes = {
        step: PropTypes.number,
        rows: PropTypes.array.isRequired,
        hourSeries: PropTypes.array.isRequired,
        recurrenceType: PropTypes.string,
        onClick: PropTypes.func,
        longLabel: PropTypes.bool,
        itemClass: PropTypes.func,
        itemProps: PropTypes.object
    };

    static defaultProps = {
        step: 2,
        recurrenceType: null,
        onClick: null,
        longLabel: false,
        itemClass: TimelineItem,
        itemProps: {},
    };

    state = {
        selectable: true
    };

    renderTimelineRow = ({availability, label, conflictIndicator, key, room}) => {
        const {hourSeries, itemClass: ItemClass, itemProps, step, recurrenceType, onClick, longLabel} = this.props;
        const minHour = hourSeries[0];
        const maxHour = hourSeries[hourSeries.length - 1];
        const columns = ((maxHour - minHour) / step) + 1;
        // TODO: Consider plan B (availability='alternatives') option when implemented
        const hasConflicts = !(_.isEmpty(availability.conflicts) && _.isEmpty(availability.preConflicts));
        return (
            <div styleName="timeline-row" key={`element-${key}`}>
                <TimelineRowLabel label={label}
                                  availability={conflictIndicator ? (hasConflicts ? 'conflict' : 'available') : null}
                                  longLabel={longLabel} />
                <div styleName="timeline-row-content" style={{flex: columns}}>
                    <ItemClass startHour={minHour} endHour={maxHour} data={availability} room={room}
                               onClick={() => {
                                   if (onClick && (!hasConflicts || recurrenceType !== 'single')) {
                                       onClick(room);
                                   }
                               }}
                               setSelectable={selectable => {
                                   this.setState({selectable});
                               }}
                               {...itemProps} />
                </div>
            </div>
        );
    };

    renderDividers = (count) => {
        const leftOffset = (100 / count);

        return (
            _.times(count + 1, (i) => (
                // eslint-disable-next-line react/no-array-index-key
                <div styleName="timeline-divider"
                     style={{left: `${(i * leftOffset)}%`}}
                     key={`divider-${i}`} />
            ))
        );
    };

    render() {
        const {rows, hourSeries, longLabel} = this.props;
        const {selectable} = this.state;
        const labelWidth = longLabel ? 200 : 150;
        return (
            <>
                <div styleName="timeline-header" className={!selectable && 'timeline-non-selectable'}>
                    <div style={{width: labelWidth}} />
                    {hourSeries.slice(0, -1).map((hour) => (
                        <div styleName="timeline-header-label" key={`timeline-header-${hour}`}>
                            <span styleName="timeline-label-text">
                                {moment({hours: hour}).format('H:mm')}
                            </span>
                        </div>
                    ))}
                </div>
                <div styleName="timeline-content" className={!selectable && 'timeline-non-selectable'}>
                    {rows.map((rowProps) => this.renderTimelineRow(rowProps))}
                    <div style={{left: labelWidth, width: `calc(100% - ${labelWidth}px)`}}
                         styleName="timeline-lines">
                        {this.renderDividers(hourSeries.length - 1, longLabel)}
                    </div>
                </div>
            </>
        );
    }
}


function TimelineRowLabel({label, availability, longLabel}) {
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
            <span>{label}</span>
        </span>
    );

    return (
        <TooltipIfTruncated>
            <div styleName="timeline-row-label" style={{width: longLabel ? 200 : 150}}>
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
};

TimelineRowLabel.defaultProps = {
    availability: null,
    longLabel: false,
};
