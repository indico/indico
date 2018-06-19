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

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {TooltipIfTruncated} from 'indico/react/components';

import TimelineItem from './TimelineItem';

import './TimelineContent.module.scss';


export default class TimelineContent extends React.Component {
    static propTypes = {
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        step: PropTypes.number,
        rows: PropTypes.array.isRequired,
        hourSeries: PropTypes.array.isRequired,
        recurrenceType: PropTypes.string,
        openModal: PropTypes.func,
    };

    static defaultProps = {
        step: 2,
        recurrenceType: null,
        openModal: null,
    };

    renderTimelineRow = ({availability, label, conflictIndicator, id, room}) => {
        const {minHour, maxHour, step, recurrenceType, openModal} = this.props;
        const columns = ((maxHour - minHour) / step) + 1;
        // TODO: Consider plan B (availability='alternatives') option when implemented
        const hasConflicts = !(_.isEmpty(availability.conflicts) && _.isEmpty(availability.preConflicts));
        return (
            <div styleName="timeline-row" key={`element-${id}`}>
                <TimelineRowLabel label={label}
                                  availability={conflictIndicator ? (hasConflicts ? 'conflict' : 'available') : null} />
                <div styleName="timeline-row-content" style={{flex: columns}}>
                    <TimelineItem step={step} startHour={minHour} endHour={maxHour} data={availability}
                                  bookable={!hasConflicts}
                                  onClick={() => {
                                      if (openModal && (!hasConflicts || recurrenceType !== 'single')) {
                                          openModal(room);
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
                <div styleName="timeline-divider" style={{left: `${(i + 1) * leftOffset}%`}} key={`divider-${i}`} />
            ))
        );
    };

    render() {
        const {rows, hourSeries} = this.props;
        return (
            <div styleName="timeline-content">
                <div styleName="timeline-header">
                    <div styleName="timeline-header-label" />
                    {hourSeries.map((hour) => (
                        <div styleName="timeline-header-label" key={`timeline-header-${hour}`}>
                            {moment({hours: hour}).format('H:mm')}
                        </div>
                    ))}
                </div>
                {rows.map((rowProps) => this.renderTimelineRow(rowProps))}
                {this.renderDividers(hourSeries.length)}
            </div>
        );
    }
}


function TimelineRowLabel({label, availability}) {
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
            <div styleName="timeline-row-label">
                <div styleName="label">
                    {availability ? <Popup trigger={roomLabel} content={tooltip} size="small" /> : roomLabel}
                </div>
            </div>
        </TooltipIfTruncated>
    );
}

TimelineRowLabel.propTypes = {
    label: PropTypes.string.isRequired,
    availability: PropTypes.oneOf(['available', 'alternatives', 'conflict'])
};

TimelineRowLabel.defaultProps = {
    availability: null,
};
