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
import {AutoSizer, List, WindowScroller} from 'react-virtualized';
import {Placeholder} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';
import {toMoment} from 'indico/utils/date';
import {TooltipIfTruncated} from 'indico/react/components';

import OccurrenceActionsDropdown from '../bookings/OccurrenceActionsDropdown';
import TimelineItem from './TimelineItem';
import EditableTimelineItem from './EditableTimelineItem';

import './TimelineContent.module.scss';


export default class DailyTimelineContent extends React.Component {
    static propTypes = {
        rows: PropTypes.array.isRequired,
        onClickCandidate: PropTypes.func,
        onClickReservation: PropTypes.func,
        longLabel: PropTypes.bool,
        onClickLabel: PropTypes.func,
        isLoading: PropTypes.bool,
        lazyScroll: PropTypes.object,
        minHour: PropTypes.number,
        maxHour: PropTypes.number,
        hourStep: PropTypes.number,
        showUnused: PropTypes.bool,
        fixedHeight: PropTypes.string,
        onAddSlot: PropTypes.func,
        renderHeader: PropTypes.func,
        showActions: PropTypes.bool,
        booking: PropTypes.object,
    };

    static defaultProps = {
        onClickCandidate: null,
        onClickReservation: null,
        longLabel: false,
        onClickLabel: null,
        isLoading: false,
        lazyScroll: null,
        minHour: 6,
        maxHour: 22,
        hourStep: 2,
        showUnused: true,
        fixedHeight: null,
        onAddSlot: null,
        renderHeader: null,
        showActions: false,
        booking: null
    };

    state = {
        selectable: true
    };

    shouldComponentUpdate(nextProps, nextState) {
        return !_.isEqual(this.props, nextProps) || !_.isEqual(this.state, nextState);
    }

    onClickLabel = (id) => {
        const {onClickLabel} = this.props;
        return onClickLabel ? () => onClickLabel(id) : false;
    };

    getEditableItem = (room) => {
        const {onAddSlot} = this.props;
        const editable = onAddSlot && (room.canUserBook || room.canUserPrebook);
        const ItemClass = editable ? EditableTimelineItem : TimelineItem;
        const itemProps = editable ? {onAddSlot} : {};
        return {ItemClass, itemProps};
    };

    renderTimelineRow({availability, label, verboseLabel, room}, key, rowStyle = null) {
        const {minHour, maxHour, hourStep, onClickCandidate, onClickReservation, longLabel, showActions} = this.props;
        const columns = ((maxHour - minHour) / hourStep) + 1;
        const hasConflicts = !(_.isEmpty(availability.conflicts) && _.isEmpty(availability.preConflicts));
        const {ItemClass, itemProps} = this.getEditableItem(room);

        return (
            <div styleName="timeline-row" key={key} style={rowStyle}>
                <TimelineRowLabel label={label}
                                  verboseLabel={verboseLabel}
                                  longLabel={longLabel}
                                  onClickLabel={this.onClickLabel(room.id)} />
                <div styleName="timeline-row-content" style={{flex: columns}}>
                    <ItemClass startHour={minHour} endHour={maxHour} data={availability} room={room}
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
                </div>
                {showActions && this.renderRowActions(availability)}
            </div>
        );
    }

    renderDividers(count, step) {
        const leftOffset = (100 / count);

        return _.range(0, count + step, step).map(i => (
            // eslint-disable-next-line react/no-array-index-key
            <div styleName="timeline-divider"
                 style={{left: `${(i * leftOffset)}%`}}
                 key={`divider-${i}`} />
        ));
    }

    renderHeader() {
        const {selectable} = this.state;
        const {renderHeader, maxHour, minHour, hourStep} = this.props;
        const hourSpan = maxHour - minHour;
        const hourSeries = _.range(minHour, maxHour + hourStep, hourStep);

        return (
            <div styleName="timeline-header" className={!selectable ? 'timeline-non-selectable' : ''}>
                {renderHeader ? renderHeader() : this.renderDefaultHeader(hourSpan, hourSeries)}
            </div>
        );
    }

    renderRowActions = (availability) => {
        const {booking} = this.props;
        if (!booking || !availability.bookings.length) {
            return;
        }
        const date = toMoment(availability.bookings[0].startDt);
        return (
            <div styleName="timeline-row-actions">
                <OccurrenceActionsDropdown booking={booking} date={date} />
            </div>
        );
    };

    renderDefaultHeader = (hourSpan, hourSeries) => {
        const {hourStep, longLabel} = this.props;
        const labelWidth = longLabel ? 200 : 150;

        return (
            <>
                <div style={{width: labelWidth}} />
                <div styleName="timeline-header-labels">
                    {_.range(0, hourSpan + hourStep, hourStep).map((i, n) => (
                        <div styleName="timeline-header-label"
                             key={`timeline-header-${i}`}
                             style={{position: 'absolute', left: `${i / hourSpan * 100}%`}}>
                            <span styleName="timeline-label-text">
                                {moment({hours: hourSeries[n]}).format('LT')}
                            </span>
                        </div>
                    ))}
                </div>
            </>
        );
    };

    renderTimelineItemPlaceholders = (props = {}) => (
        _.range(0, 10).map((i) => (
            <Placeholder {...props} key={i} styleName="timeline-item-placeholder" fluid>
                <Placeholder.Paragraph>
                    <Placeholder.Line />
                </Placeholder.Paragraph>
            </Placeholder>
        ))
    );

    renderList(hourSpan, width, height = null, extraProps = {}) {
        const {rows, hourStep, longLabel, isLoading} = this.props;
        const {selectable} = this.state;
        const labelWidth = longLabel ? 200 : 150;
        const rowHeight = 50;

        return (
            <>
                <div styleName="timeline-content"
                     className={!selectable ? 'timeline-non-selectable' : ''}
                     style={{width}}>
                    <div style={{left: labelWidth, width: `calc(100% - ${labelWidth}px)`}}
                         styleName="timeline-lines">
                        {this.renderDividers(hourSpan, hourStep)}
                    </div>
                    <div>
                        <List width={width}
                              height={height || rows.length * rowHeight}
                              rowCount={rows.length}
                              overscanRowCount={15}
                              rowHeight={50}
                              noRowsRenderer={this.renderTimelineItemPlaceholders}
                              rowRenderer={({index, style, key}) => (
                                  this.renderTimelineRow(rows[index], key, style)
                              )}
                              {...extraProps}
                              tabIndex={null} />
                    </div>
                </div>
                {rows.length !== 0 && isLoading && this.renderTimelineItemPlaceholders({style: {width}})}
            </>
        );
    }

    render() {
        const {
            rows, lazyScroll, fixedHeight, isLoading, maxHour, minHour,
        } = this.props;
        const WrapperComponent = lazyScroll ? LazyScroll : React.Fragment;
        const wrapperProps = lazyScroll || {};
        const hourSpan = maxHour - minHour;

        const windowScrollerWrapper = (
            <WindowScroller>
                {({height, isScrolling, onChildScroll, scrollTop}) => (
                    <AutoSizer disableHeight>
                        {({width}) => (
                            this.renderList(hourSpan, width, height, {
                                isScrolling,
                                scrollTop,
                                onScroll: onChildScroll,
                                autoHeight: true
                            })
                        )}
                    </AutoSizer>
                )}
            </WindowScroller>
        );

        const autoSizerWrapper = h => (
            <div style={{height: h}} styleName="auto-sizer-wrapper">
                <AutoSizer>
                    {({width}) => (
                        this.renderList(hourSpan, width)
                    )}
                </AutoSizer>
            </div>
        );

        return (
            <>
                {(isLoading || !!rows.length) && this.renderHeader()}
                <WrapperComponent {...wrapperProps}>
                    {(fixedHeight ? (
                        autoSizerWrapper(fixedHeight)
                    ) : (
                        windowScrollerWrapper
                    ))}
                </WrapperComponent>
            </>
        );
    }
}

export function TimelineRowLabel({label, verboseLabel, longLabel, onClickLabel}) {
    const labelContent = verboseLabel ? (
        <span styleName="split-label">
            <div>
                {label}
            </div>
            <TooltipIfTruncated>
                <div styleName="sub-label">
                    <small>{verboseLabel}</small>
                </div>
            </TooltipIfTruncated>
        </span>
    ) : (
        <span>{label}</span>
    );

    const roomLabel = (
        <span>
            {onClickLabel ? <a onClick={onClickLabel}>{labelContent}</a> : labelContent}
        </span>
    );
    const width = longLabel ? 200 : 150;

    return (
        <div styleName="timeline-row-label" style={{
            minWidth: width,
            maxWidth: width
        }}>
            <div styleName="label">
                {roomLabel}
            </div>
        </div>
    );
}

TimelineRowLabel.propTypes = {
    label: PropTypes.string.isRequired,
    verboseLabel: PropTypes.string,
    longLabel: PropTypes.bool,
    onClickLabel: PropTypes.oneOfType([
        PropTypes.func,
        PropTypes.bool
    ])
};

TimelineRowLabel.defaultProps = {
    longLabel: false,
    onClickLabel: null,
    verboseLabel: null,
};
