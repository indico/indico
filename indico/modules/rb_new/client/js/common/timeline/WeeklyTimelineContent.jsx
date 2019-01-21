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
import PropTypes from 'prop-types';
import React from 'react';
import {toMoment} from 'indico/utils/date';
import {toClasses} from 'indico/react/util';
import DailyTimelineContent, {TimelineRowLabel} from './DailyTimelineContent';

/* eslint-disable no-unused-vars */
import baseStyle from './TimelineContent.module.scss';
import style from './WeeklyTimelineContent.module.scss';
/* eslint-enable no-unused-vars */

export default class WeeklyTimelineContent extends DailyTimelineContent {
    static propTypes = {
        ...DailyTimelineContent.propTypes,
        dateRange: PropTypes.array.isRequired,
    };

    get dates() {
        const {rows} = this.props;
        const [row] = rows;
        return row ? row.availability.map(([dt]) => dt) : [];
    }

    renderTimelineRow({availability, room, label, conflictIndicator}, key, rowStyle = null) {
        const {minHour, maxHour, longLabel, onClickReservation, onClickCandidate} = this.props;
        const hasConflicts = availability.some(([, {conflicts}]) => !!conflicts.length);
        const {ItemClass, itemProps} = this.getEditableItem(room);

        return (
            <div styleName="baseStyle.timeline-row" key={key} style={rowStyle}>
                <TimelineRowLabel label={label}
                                  availability={conflictIndicator ? (hasConflicts ? 'conflict' : 'available') : null}
                                  longLabel={longLabel}
                                  onClickLabel={this.onClickLabel(room.id)} />
                <div styleName="style.timeline-row-content">
                    {availability.map(([dt, data]) => (
                        <ItemClass key={dt}
                                   startHour={minHour}
                                   endHour={maxHour}
                                   data={data}
                                   room={room}
                                   onClickReservation={onClickReservation}
                                   onClickCandidate={() => {
                                       if (onClickCandidate && !hasConflicts) {
                                           onClickCandidate(room);
                                       }
                                   }}
                                   setSelectable={selectable => {
                                       this.setState({selectable});
                                   }}
                                   {...itemProps} />
                    ))}
                </div>
            </div>
        );
    }

    renderDividers(hourSpan, hourStep) {
        const {rows} = this.props;
        const daySize = (100 / 7);

        if (!rows.length) {
            return null;
        }

        const {dateRange} = this.props;
        const emptyDays = this.dates
            .filter(day => dateRange.length !== 0 && !dateRange.includes(day))
            .map(day => this.dates.findIndex((el) => el === day));

        return (
            _.times(7, n => (
                <div styleName="style.timeline-day-divider"
                     className={toClasses({hidden: emptyDays.includes(n), visible: !emptyDays.includes(n)})}
                     style={{left: `${n * daySize}%`, width: `${daySize}%`}}
                     key={`day-divider-${n}`}>
                    {emptyDays.includes(n) || super.renderDividers(hourSpan, hourStep)}
                </div>
            ))
        );
    }

    renderHeader() {
        const {longLabel, selectable} = this.props;
        const labelWidth = longLabel ? 200 : 150;
        return (
            <>
                <div styleName="baseStyle.timeline-header" className={!selectable ? 'timeline-non-selectable' : ''}>
                    <div style={{minWidth: labelWidth}} />
                    <div styleName="style.timeline-header-labels">
                        {_.map(this.dates, (dt, n) => (
                            <div styleName="style.timeline-header-label"
                                 key={`timeline-header-${n}`}>
                                <span styleName="style.timeline-label-text">
                                    {toMoment(dt, 'YYYY-MM-DD').format('ddd D MMM')}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </>
        );
    }
}
