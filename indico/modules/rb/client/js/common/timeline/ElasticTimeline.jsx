// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {dayRange, getWeekday, serializeDate, toMoment} from 'indico/utils/date';

import DailyTimelineContent from './DailyTimelineContent';
import MonthlyTimelineContent from './MonthlyTimelineContent';
import WeeklyTimelineContent from './WeeklyTimelineContent';

import './Timeline.module.scss';

/**
 * An *elastic* implementation of a Timeline, which can provide
 * an overview by day, week or month.
 */
export default class ElasticTimeline extends React.Component {
  static propTypes = {
    availability: PropTypes.array.isRequired,
    datePicker: PropTypes.object.isRequired,
    bookingAllowed: PropTypes.bool,
    isLoading: PropTypes.bool,
    onAddSlot: PropTypes.func,
    onClickLabel: PropTypes.func,
    onClickCandidate: PropTypes.func,
    onClickReservation: PropTypes.func,
    longLabel: PropTypes.bool,
    emptyMessage: PropTypes.node,
    lazyScroll: PropTypes.object,
    extraContent: PropTypes.node,
    showUnused: PropTypes.bool,
    fixedHeight: PropTypes.string,
    roomTimelineAction: PropTypes.bool,
    setDate: PropTypes.func.isRequired,
    setMode: PropTypes.func.isRequired,
  };

  static defaultProps = {
    emptyMessage: (
      <Message warning>
        <Translate>No occurrences found</Translate>
      </Message>
    ),
    onClickCandidate: null,
    onClickReservation: null,
    bookingAllowed: false,
    extraContent: null,
    isLoading: false,
    onAddSlot: null,
    longLabel: false,
    onClickLabel: null,
    lazyScroll: null,
    showUnused: true,
    fixedHeight: null,
    roomTimelineAction: false,
  };

  _getDayRowSerializer(dt) {
    const {
      bookingAllowed,
      datePicker: {dateRange},
    } = this.props;
    return ({
      candidates,
      conflictingCandidates,
      concurrentPreBookings,
      preBookings,
      bookings,
      preConflicts,
      conflicts,
      blockings,
      overridableBlockings,
      nonbookablePeriods,
      unbookableHours,
      cancellations,
      rejections,
    }) => {
      const hasConflicts = !!(conflicts[dt] || []).length;
      return {
        candidates: candidates[dt]
          ? [{...candidates[dt][0], bookable: bookingAllowed && !hasConflicts}]
          : [],
        conflictingCandidates: conflictingCandidates[dt] || [],
        concurrentPreBookings: concurrentPreBookings[dt] || [],
        preBookings: preBookings[dt] || [],
        bookings: bookings[dt] || [],
        conflicts: conflicts[dt] || [],
        preConflicts: preConflicts[dt] || [],
        blockings: blockings[dt] || [],
        overridableBlockings: overridableBlockings[dt] || [],
        nonbookablePeriods: nonbookablePeriods[dt] || [],
        unbookableHours:
          dateRange.length !== 0 && !dateRange.includes(dt) ? [] : unbookableHours[getWeekday(dt)],
        cancellations: cancellations[dt] || [],
        rejections: rejections[dt] || [],
      };
    };
  }

  calcDailyRows() {
    const {
      availability,
      datePicker: {selectedDate},
    } = this.props;

    return availability
      .map(([, data]) => data)
      .map(data => ({
        availability: this._getDayRowSerializer(selectedDate)(data),
        label: data.room.name,
        verboseLabel: data.room.verboseName,
        key: data.room.id,
        room: data.room,
      }));
  }

  calcWeeklyRows() {
    const {
      availability,
      datePicker: {selectedDate},
    } = this.props;
    const weekStart = toMoment(selectedDate, 'YYYY-MM-DD').startOf('week');
    const weekRange = [...Array(7).keys()].map(n =>
      serializeDate(weekStart.clone().add(n, 'days'))
    );

    if (!availability.length) {
      return [];
    }

    return availability.map(([, data]) => {
      const {room} = data;
      return {
        availability: weekRange.map(dt => [dt, this._getDayRowSerializer(dt)(data)]),
        label: room.name,
        verboseLabel: room.verboseName,
        key: room.id,
        room,
      };
    });
  }

  calcMonthlyRows() {
    const {
      availability,
      datePicker: {selectedDate},
    } = this.props;
    const date = toMoment(selectedDate, 'YYYY-MM-DD');
    const monthStart = date.clone().startOf('month');
    const monthEnd = date.clone().endOf('month');
    const monthRange = dayRange(monthStart, monthEnd).map(d => d.format('YYYY-MM-DD'));
    if (!availability.length) {
      return [];
    }

    return availability.map(([, data]) => {
      const {room} = data;
      return {
        availability: monthRange.map(dt => [dt, this._getDayRowSerializer(dt)(data)]),
        label: room.name,
        verboseLabel: room.verboseName,
        key: room.id,
        room,
      };
    });
  }

  hasUsage = availability => {
    const fields = ['preBookings', 'bookings', 'candidates'];
    return fields.some(field => !_.isEmpty(availability[field]));
  };

  /** Filter out rooms that are not used at all */
  filterUnused(rows, mode) {
    if (mode === 'days') {
      return rows.filter(({availability: av}) => this.hasUsage(av));
    } else {
      return rows.filter(({availability: av}) => av.some(([, a]) => this.hasUsage(a)));
    }
  }

  renderTimeline = () => {
    const {
      extraContent,
      onClickCandidate,
      onClickReservation,
      availability,
      isLoading,
      onAddSlot,
      longLabel,
      onClickLabel,
      lazyScroll,
      datePicker: {minHour, maxHour, hourStep, mode, dateRange},
      showUnused,
      fixedHeight,
      emptyMessage,
      roomTimelineAction,
      setDate,
      setMode,
    } = this.props;
    let Component = DailyTimelineContent;
    let rows = this.calcDailyRows(availability);
    const componentProps = {};

    if (mode === 'weeks') {
      Component = WeeklyTimelineContent;
      rows = this.calcWeeklyRows(availability);
    } else if (mode === 'months') {
      Component = MonthlyTimelineContent;
      rows = this.calcMonthlyRows(availability);
    }

    if (mode === 'weeks' || mode === 'months') {
      componentProps.dateRange = dateRange;
    }

    if (!showUnused) {
      rows = this.filterUnused(rows, mode);
    }

    if (!rows.length && !isLoading) {
      return emptyMessage;
    }

    return (
      <div styleName="timeline">
        {extraContent}
        <Component
          {...componentProps}
          rows={rows}
          minHour={minHour}
          maxHour={maxHour}
          hourStep={hourStep}
          onClickCandidate={onClickCandidate}
          onClickReservation={onClickReservation}
          onAddSlot={onAddSlot}
          longLabel={longLabel}
          onClickLabel={onClickLabel}
          isLoading={isLoading}
          lazyScroll={lazyScroll}
          showUnused={showUnused}
          fixedHeight={fixedHeight}
          rowActions={{roomTimeline: roomTimelineAction}}
          setDate={setDate}
          setMode={setMode}
          gutterAllowed
        />
      </div>
    );
  };

  render() {
    const {emptyMessage, isLoading, availability} = this.props;
    if (!isLoading && !availability.length) {
      return emptyMessage;
    }
    return this.renderTimeline();
  }
}
