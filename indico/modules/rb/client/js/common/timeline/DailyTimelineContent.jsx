// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {AutoSizer, List, WindowScroller} from 'react-virtualized';
import {Icon, Message, Popup, Placeholder} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';
import Overridable from 'react-overridable';

import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';
import {TooltipIfTruncated} from 'indico/react/components';
import {Responsive} from 'indico/react/util';

import RowActionsDropdown from './RowActionsDropdown';
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
    rowActions: PropTypes.objectOf(PropTypes.bool),
    booking: PropTypes.object,
    gutterAllowed: PropTypes.bool,
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
    rowActions: {
      occurrence: false,
      roomTimeline: false,
    },
    booking: null,
    gutterAllowed: false,
  };

  state = {
    selectable: true,
  };

  shouldComponentUpdate(nextProps, nextState) {
    return !_.isEqual(this.props, nextProps) || !_.isEqual(this.state, nextState);
  }

  onClickLabel = id => {
    const {onClickLabel} = this.props;
    return onClickLabel ? () => onClickLabel(id) : false;
  };

  getEditableItem = room => {
    const {onAddSlot} = this.props;
    const editable = onAddSlot && (room.canUserBook || room.canUserPrebook);
    const ItemClass = editable ? EditableTimelineItem : TimelineItem;
    const itemProps = editable ? {onAddSlot} : {};
    return {ItemClass, itemProps};
  };

  renderRowLabel = (rowLabelProps, room) => {
    return (
      <Overridable id="TimelineContent.rowLabel" room={room} {...rowLabelProps}>
        <TimelineRowLabel {...rowLabelProps} />
      </Overridable>
    );
  };

  hasOccurrenceActions = booking => {
    return Object.values(booking.occurrences.bookings).some(([occ]) => {
      return occ && (occ.canCancel || occ.canReject);
    });
  };

  get hasActions() {
    const {booking, rowActions} = this.props;
    const hasOccurrenceActions = rowActions.occurrence ? this.hasOccurrenceActions(booking) : false;
    return rowActions.roomTimeline || hasOccurrenceActions;
  }

  renderTimelineRow({availability, label, verboseLabel, room}, key, hasActions, rowStyle = null) {
    const {
      minHour,
      maxHour,
      onClickCandidate,
      onClickReservation,
      longLabel,
      gutterAllowed,
    } = this.props;

    const hasConflicts = !_.isEmpty(availability.conflicts);
    const {ItemClass, itemProps} = this.getEditableItem(room);
    const rowLabelProps = {
      label,
      verboseLabel,
      longLabel,
      gutterAllowed,
      onClickLabel: this.onClickLabel(room.id),
    };

    return (
      <div styleName="timeline-row" key={key} style={rowStyle}>
        {this.renderRowLabel(rowLabelProps, room)}
        <div styleName="timeline-row-content">
          <ItemClass
            startHour={minHour}
            endHour={maxHour}
            data={availability}
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
            {...itemProps}
          />
        </div>
        {hasActions && (
          <div styleName="timeline-row-actions">{this.renderRowActions(availability, room)}</div>
        )}
      </div>
    );
  }

  renderDividers(count, step) {
    const leftOffset = 100 / count;

    return _.range(0, count + step, step).map(i => (
      // eslint-disable-next-line react/no-array-index-key
      <div styleName="timeline-divider" style={{left: `${i * leftOffset}%`}} key={`divider-${i}`} />
    ));
  }

  renderHeader() {
    const {selectable} = this.state;
    const {renderHeader, maxHour, minHour, hourStep} = this.props;
    const hourSpan = maxHour - minHour;
    const hourSeries = _.range(minHour, maxHour + hourStep, hourStep);

    return (
      <div styleName="timeline-header" className={!selectable ? 'timeline-non-selectable' : ''}>
        {renderHeader
          ? renderHeader()
          : this.renderDefaultHeader(hourSpan, hourSeries, this.hasActions)}
      </div>
    );
  }

  renderRowActions = (availability, room) => {
    const {booking, rowActions} = this.props;
    let props = {};
    if (rowActions.occurrence && booking && availability.bookings.length) {
      props = {date: toMoment(availability.bookings[0].startDt), booking};
    }
    if (rowActions.roomTimeline) {
      props = {...props, room};
    }
    return <RowActionsDropdown {...props} />;
  };

  renderDefaultHeader = (hourSpan, hourSeries, hasActions) => {
    const {hourStep, longLabel} = this.props;
    const labelWidth = longLabel ? 200 : 150;

    return (
      <>
        <div style={{width: labelWidth}} />
        <div styleName="timeline-header-labels">
          {_.range(0, hourSpan + hourStep, hourStep).map((i, n) => (
            <div
              styleName="timeline-header-label"
              key={`timeline-header-${i}`}
              style={{position: 'absolute', left: `${(i / hourSpan) * 100}%`}}
            >
              <span styleName="timeline-label-text">
                {moment({hours: hourSeries[n]}).format('LT')}
              </span>
            </div>
          ))}
        </div>
        {hasActions && <div styleName="timeline-header-actions" />}
      </>
    );
  };

  renderTimelineItemPlaceholders = (props = {}) =>
    _.range(0, 10).map(i => (
      <Placeholder {...props} key={i} styleName="timeline-item-placeholder" fluid>
        <Placeholder.Paragraph>
          <Placeholder.Line />
        </Placeholder.Paragraph>
      </Placeholder>
    ));

  renderList(hourSpan, hasActions, width, height = null, extraProps = {}) {
    const {rows, hourStep, longLabel, isLoading} = this.props;
    const {selectable} = this.state;
    const labelWidth = longLabel ? 200 : 150;
    const actionsWidth = hasActions ? 70 : 0;
    const rowHeight = 50;

    return (
      <>
        <div
          styleName="timeline-content"
          className={!selectable ? 'timeline-non-selectable' : ''}
          style={{width}}
        >
          <div
            style={{
              left: labelWidth,
              width: `calc(100% - ${labelWidth}px - ${actionsWidth}px - 2em)`,
            }}
            styleName="timeline-lines"
          >
            {this.renderDividers(hourSpan, hourStep)}
          </div>
          <div>
            <List
              width={width}
              height={height || rows.length * rowHeight}
              rowCount={rows.length}
              overscanRowCount={15}
              rowHeight={50}
              noRowsRenderer={this.renderTimelineItemPlaceholders}
              rowRenderer={({index, style, key}) =>
                this.renderTimelineRow(rows[index], key, hasActions, style)
              }
              {...extraProps}
              tabIndex={null}
            />
          </div>
        </div>
        {rows.length !== 0 && isLoading && this.renderTimelineItemPlaceholders({style: {width}})}
      </>
    );
  }

  render() {
    const {rows, lazyScroll, fixedHeight, isLoading, maxHour, minHour} = this.props;
    const WrapperComponent = lazyScroll ? LazyScroll : React.Fragment;
    const wrapperProps = lazyScroll || {};
    const hourSpan = maxHour - minHour;
    const hasActions = this.hasActions;

    const windowScrollerWrapper = (
      <WindowScroller>
        {({height, isScrolling, onChildScroll, scrollTop}) => (
          <AutoSizer disableHeight>
            {({width}) =>
              this.renderList(hourSpan, hasActions, width, height, {
                isScrolling,
                scrollTop,
                onScroll: onChildScroll,
                autoHeight: true,
              })
            }
          </AutoSizer>
        )}
      </WindowScroller>
    );

    const autoSizerWrapper = h => (
      <div style={{height: h}} styleName="auto-sizer-wrapper">
        <AutoSizer>{({width}) => this.renderList(hourSpan, hasActions, width)}</AutoSizer>
      </div>
    );

    const timeline = (
      <div styleName="daily-timeline">
        {(isLoading || !!rows.length) && this.renderHeader()}
        <WrapperComponent {...wrapperProps}>
          {fixedHeight ? autoSizerWrapper(fixedHeight) : windowScrollerWrapper}
        </WrapperComponent>
      </div>
    );

    return (
      <Responsive.Portrait orElse={timeline}>
        <Responsive.Phone andSmaller orElse={timeline}>
          <Message icon info>
            <Icon name="mobile alternate" styleName="rotate-icon" />
            <Message.Content>
              <Translate>Please turn your device horizontally to view this page.</Translate>
            </Message.Content>
          </Message>
        </Responsive.Phone>
      </Responsive.Portrait>
    );
  }
}

export function TimelineRowLabel({
  label,
  verboseLabel,
  longLabel,
  onClickLabel,
  gutterAllowed,
  gutter,
  gutterTooltip,
}) {
  const width = longLabel ? 200 : 150;
  const hasGutter = gutterAllowed && gutter;
  const labelContent = verboseLabel ? (
    <span styleName="split-label">
      <div>{label}</div>
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
    <div styleName={`label ${hasGutter ? 'gutter' : ''}`}>
      {onClickLabel ? <a onClick={onClickLabel}>{labelContent}</a> : labelContent}
    </div>
  );

  return (
    <div
      styleName="timeline-row-label"
      style={{
        minWidth: width,
        maxWidth: width,
      }}
    >
      {hasGutter && gutterTooltip ? (
        <Popup trigger={roomLabel} content={gutterTooltip} position="left center" />
      ) : (
        roomLabel
      )}
    </div>
  );
}

TimelineRowLabel.propTypes = {
  label: PropTypes.string.isRequired,
  verboseLabel: PropTypes.string,
  longLabel: PropTypes.bool,
  gutterAllowed: PropTypes.bool,
  gutter: PropTypes.bool,
  gutterTooltip: PropTypes.string,
  onClickLabel: PropTypes.oneOfType([PropTypes.func, PropTypes.bool]),
};

TimelineRowLabel.defaultProps = {
  longLabel: false,
  verboseLabel: null,
  gutterAllowed: false,
  gutter: false,
  gutterTooltip: '',
  onClickLabel: null,
};
