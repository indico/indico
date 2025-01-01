// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';

import {toClasses} from 'indico/react/util';
import {toMoment} from 'indico/utils/date';

import WeeklyTimelineContent from './DailyTimelineContent';

/* eslint-disable no-unused-vars */
import baseStyle from './TimelineContent.module.scss';
import style from './WeeklyTimelineContent.module.scss';
/* eslint-enable no-unused-vars */

export default class MonthlyTimelineContent extends WeeklyTimelineContent {
  get dates() {
    const {rows} = this.props;
    if (rows.length) {
      return rows[0].availability.map(([dt]) => dt);
    }
    return [];
  }

  get weekendDays() {
    return this.dates
      .filter(day => [6, 7].includes(toMoment(day, 'YYYY-MM-DD').isoWeekday()))
      .map(day => this.dates.findIndex(el => el === day));
  }

  renderTimelineRow({availability, room, label, verboseLabel}, key, hasActions, rowStyle = null) {
    const {
      minHour,
      maxHour,
      longLabel,
      onClickCandidate,
      onClickReservation,
      gutterAllowed,
    } = this.props;
    const hasConflicts = availability.some(([, {conflicts}]) => !!conflicts.length);
    const {ItemClass, itemProps} = this.getEditableItem(room);
    const rowLabelProps = {
      label,
      verboseLabel,
      longLabel,
      gutterAllowed,
      onClickLabel: this.onClickLabel(room.id),
    };

    return (
      <div styleName="baseStyle.timeline-row" key={key} style={rowStyle}>
        {this.renderRowLabel(rowLabelProps, room)}
        <div styleName="style.timeline-row-content">
          {availability.map(([dt, data]) => (
            <ItemClass
              key={dt}
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
              {...itemProps}
            />
          ))}
        </div>
        {this.hasActions && (
          <div styleName="baseStyle.timeline-row-actions">
            {this.renderRowActions(availability, room)}
          </div>
        )}
      </div>
    );
  }

  renderDividers() {
    const nDays = this.dates.length;
    const daySize = 100 / nDays;
    const {dateRange} = this.props;
    const emptyDays = this.dates
      .filter(day => dateRange.length !== 0 && !dateRange.includes(day))
      .map(day => this.dates.findIndex(el => el === day));

    return _.times(nDays, n => {
      const indicateWeekend = this.weekendDays.includes(n) && !emptyDays.includes(n);
      const dividerStyle = 'style.timeline-day-divider';
      return (
        <div
          styleName={indicateWeekend ? `${dividerStyle} style.weekend` : dividerStyle}
          className={toClasses({hidden: emptyDays.includes(n), visible: !emptyDays.includes(n)})}
          style={{left: `${n * daySize}%`, width: `${daySize}%`}}
          key={`day-divider-${n}`}
        />
      );
    });
  }

  renderHeader() {
    const {longLabel, selectable, setDate, setMode} = this.props;
    const labelWidth = longLabel ? 200 : 150;

    return (
      <div
        styleName="baseStyle.timeline-header"
        className={!selectable ? 'timeline-non-selectable' : ''}
      >
        <div style={{minWidth: labelWidth}} />
        <div styleName="style.timeline-header-labels">
          {this.dates.map((dt, n) => {
            const indicateWeekend = this.weekendDays.includes(n);
            return (
              <div
                className={`${style['timeline-header-label']} monthly ${
                  indicateWeekend ? style.weekend : ''
                }`}
                key={`timeline-header-${dt}`}
              >
                <span
                  styleName="style.timeline-label-text"
                  onClick={() => {
                    setDate(dt);
                    setMode('days');
                  }}
                >
                  {toMoment(dt, 'YYYY-MM-DD').format('D')}
                </span>
              </div>
            );
          })}
        </div>
        {this.hasActions && <div styleName="baseStyle.timeline-header-actions" />}
      </div>
    );
  }
}
