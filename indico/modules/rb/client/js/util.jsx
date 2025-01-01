// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {push} from 'connected-react-router';
import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Popup} from 'semantic-ui-react';

import {PluralTranslate, Translate, Param} from 'indico/react/i18n';
import {Responsive} from 'indico/react/util';
import {serializeDate} from 'indico/utils/date';

export function preProcessParameters(params, rules) {
  return _pruneNullLeaves(
    Object.assign(
      ...Object.entries(rules).map(([k, rule]) => {
        if (typeof rule === 'object') {
          const {serializer, onlyIf} = rule;
          rule = serializer;
          if (!onlyIf(params)) {
            return {};
          }
        }
        const value = rule(params);
        if (value === undefined) {
          return {};
        }
        return {[k]: value};
      })
    )
  );
}

function calculateDefaultEndDate(startDate, type, number, interval) {
  const isMoment = moment.isMoment(startDate);
  const dt = isMoment ? startDate.clone() : moment(startDate);

  if (type === 'daily') {
    dt.add(1, 'weeks');
  } else if (interval === 'week') {
    // 5 occurrences
    dt.add(4 * number, 'weeks');
  } else {
    // 7 occurences
    dt.add(6 * number, 'months');
  }
  return isMoment ? dt : serializeDate(dt);
}

export function sanitizeRecurrence(filters) {
  const {
    dates: {endDate, startDate},
    recurrence: {type, interval, number},
  } = filters;

  if (type === 'single' && endDate) {
    filters.dates = {...filters.dates, endDate: null};
  } else if (type !== 'single' && startDate && !endDate) {
    // if there's a start date already set, let's set a sensible
    // default for the end date
    filters.dates = {
      ...filters.dates,
      endDate: calculateDefaultEndDate(startDate, type, number, interval),
    };
  }
}

function _pruneNullLeaves(obj) {
  if (!Object.entries(obj).length) {
    return {};
  }

  return Object.assign(
    ...Object.entries(obj).map(([k, v]) => {
      if (v === null) {
        return {};
      } else if (Array.isArray(v)) {
        return {[k]: v.filter(e => e !== null)};
      } else if (typeof v === 'object') {
        return {[k]: _pruneNullLeaves(v)};
      } else {
        return {[k]: v};
      }
    })
  );
}

export const pushStateMergeProps = (stateProps, dispatchProps, ownProps) => {
  const {dispatch, ...realDispatchProps} = dispatchProps;
  return {
    ...ownProps,
    ...stateProps,
    ...realDispatchProps,
    pushState(url, restoreQueryString = false) {
      if (restoreQueryString) {
        url += `?${stateProps.queryString}`;
      }
      dispatch(push(url));
    },
  };
};

/**
 * Defines a query string state field for a boolean that is only added
 * to the query string if it's true.
 * @param {string} name - Name of the state field.
 */
export function boolStateField(name) {
  return {
    serialize: state => _.get(state, name) || null,
    parse: (value, state) => {
      _.set(state, name, value);
    },
  };
}

/**
 * Defines a query string state field that is only added to the query
 * string if the value doesn't match the default.
 * @param {string} name - Name of the state field.
 * @param defaultValue - The default value that will not go to the query string.
 */
export function defaultStateField(name, defaultValue) {
  return {
    serialize: state => {
      const value = _.get(state, name, null);
      return value === defaultValue ? null : value;
    },
    parse: (value, state) => {
      _.set(state, name, value);
    },
  };
}

export function isDateWithinRange(date, dateRange, _toMoment) {
  return date && dateRange.filter(dt => _toMoment(dt).isSame(date, 'day')).length !== 0;
}

export function PopupParam({content, children}) {
  const trigger = <span>{children}</span>;
  return <Popup trigger={trigger} content={content} position="right center" />;
}

PopupParam.propTypes = {
  content: PropTypes.object.isRequired,
  children: PropTypes.object,
};

PopupParam.defaultProps = {
  children: null,
};

export function renderRecurrence({type, number, interval}, shortcut = true) {
  if (!type) {
    return null;
  }
  if (type === 'single') {
    return (
      <Responsive.Tablet andSmaller onlyIf={shortcut} orElse={Translate.string('Once')}>
        <Translate context="single booking shortcut">S</Translate>
      </Responsive.Tablet>
    );
  } else if (type === 'daily') {
    return (
      <Responsive.Tablet andSmaller onlyIf={shortcut} orElse={Translate.string('Daily')}>
        <Translate context="daily booking shortcut">D</Translate>
      </Responsive.Tablet>
    );
  } else if (interval === 'week') {
    return (
      <Responsive.Tablet
        andSmaller
        onlyIf={shortcut}
        orElse={PluralTranslate.string('Weekly', 'Every {number} weeks', number, 'repetition', {
          number,
        })}
      >
        <Translate context="weekly booking shortcut">
          <Param name="number" value={number > 1 ? number : ''} />W
        </Translate>
      </Responsive.Tablet>
    );
  } else {
    return (
      <Responsive.Tablet
        andSmaller
        onlyIf={shortcut}
        orElse={PluralTranslate.string('Monthly', 'Every {number} months', number, 'repetition', {
          number,
        })}
      >
        <Translate context="monthly booking shortcut">
          <Param name="number" value={number > 1 ? number : ''} />M
        </Translate>
      </Responsive.Tablet>
    );
  }
}

export function getRecurrenceInfo(repetition) {
  const [repeatFrequency, repeatInterval, recurrenceWeekdays] = repetition;
  let type = 'single';
  let number = '1';
  let interval = 'week';
  let weekdays = [];
  if (repeatFrequency === 1) {
    type = 'daily';
  } else if (repeatFrequency === 2) {
    type = 'every';
    interval = 'week';
    number = repeatInterval;
    weekdays = recurrenceWeekdays;
  } else if (repeatFrequency === 3) {
    type = 'every';
    interval = 'month';
    number = repeatInterval;
  }
  return {type, number, interval, weekdays};
}

export function serializeRecurrenceInfo({type, number, interval}) {
  if (type === 'single') {
    return ['NEVER', 0];
  } else if (type === 'daily') {
    return ['DAY', 1];
  } else if (interval === 'week') {
    return ['WEEK', number];
  } else if (interval === 'month') {
    return ['MONTH', number];
  }
}

/**
 * Renders the array of recurrence weekdays into a nicely formatted string
 * @param {object} opts Options
 * @param {array} opts.weekdays Array of weekdays
 * @param {number} opts.repetition Recurrence repetition (e.g. every `2` weeks)
 * @param {boolean} opts.weekdaysOnly Whether to return only the weekdays
 * @returns {string} Formatted string of weekdays
 */
export function renderRecurrenceWeekdays({weekdays, repetition = null, weekdaysOnly = false}) {
  const weekdaysMap = {
    mon: moment.weekdays(1),
    tue: moment.weekdays(2),
    wed: moment.weekdays(3),
    thu: moment.weekdays(4),
    fri: moment.weekdays(5),
    sat: moment.weekdays(6),
    sun: moment.weekdays(0),
  };

  if (weekdays === null || weekdays.length === 0) {
    return null;
  }

  // handle unknown/bad weekdays
  if (weekdays.some(weekday => !Object.keys(weekdaysMap).includes(weekday))) {
    return null;
  }

  const orderedWeekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

  // sort the weekdays based on their position in the orderedWeekdays array
  const sortedWeekdays = weekdays.sort(
    (a, b) => orderedWeekdays.indexOf(a) - orderedWeekdays.indexOf(b)
  );

  const formattedWeekdays = new Intl.ListFormat(moment.locale(), {
    style: 'long',
    type: 'conjunction',
  }).format(sortedWeekdays.map(weekday => weekdaysMap[weekday]));

  // only show the repetition if it's greater than 1
  if (repetition && repetition > 1) {
    return PluralTranslate.string(
      'Every week on {weekdays}',
      'Every {repetition} weeks on {weekdays}',
      repetition,
      {
        repetition,
        weekdays: formattedWeekdays,
      }
    );
  }

  if (weekdaysOnly) {
    return formattedWeekdays;
  }

  return Translate.string('Every {weekdays}', {weekdays: formattedWeekdays});
}

const _legendLabels = {
  candidates: {label: Translate.string('Available'), style: 'available'},
  bookings: {label: Translate.string('Booking'), style: 'booking'},
  preBookings: {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
  conflicts: {label: Translate.string('Conflict'), style: 'conflict'},
  preConflicts: {
    label: Translate.string('Conflict with Pre-Booking'),
    style: 'pre-booking-conflict',
  },
  conflictingCandidates: {
    label: Translate.string('Invalid occurrence'),
    style: 'conflicting-candidate',
  },
  other: {label: Translate.string('Other booking'), style: 'other'},
  rejections: {label: Translate.string('Rejected', 'Booking'), style: 'rejection'},
  cancellations: {label: Translate.string('Cancelled', 'Booking'), style: 'cancellation'},
  pendingCancellations: {
    label: Translate.string('Will be cancelled', 'Booking'),
    style: 'pending-cancellation',
  },
  blockings: {label: Translate.string('Blocking'), style: 'blocking'},
  overridableBlockings: {
    label: Translate.string('Blocking (allowed)'),
    style: 'overridable-blocking',
  },
  nonbookablePeriods: {label: Translate.string('Not bookable'), style: 'unbookable'},
  unbookableHours: {label: Translate.string('Not bookable'), style: 'unbookable'},
  concurrentPreBookings: {
    label: Translate.string('Concurrent Pre-Bookings'),
    style: 'concurrent-pre-booking',
  },
};

const _orderedLabels = [
  'candidates',
  'bookings',
  'preBookings',
  'concurrentPreBookings',
  'conflicts',
  'preConflicts',
  'conflictingCandidates',
  'rejections',
  'cancellations',
  'pendingCancellations',
  'other',
  'blockings',
  'overridableBlockings',
  'nonbookablePeriods',
  'unbookableHours',
];

export function transformToLegendLabels(occurrenceTypes, inactiveTypes = []) {
  return _orderedLabels.reduce((legend, type) => {
    const label = _legendLabels[type];
    if (
      occurrenceTypes.includes(type) &&
      !inactiveTypes.includes(type) &&
      !legend.some(legendLabel => legendLabel.style === label.style)
    ) {
      legend.push(_legendLabels[type]);
    }
    return legend;
  }, []);
}

export function getOccurrenceTypes(availability) {
  return Object.entries(availability).reduce((occurrenceTypes, [type, occurrences]) => {
    if (occurrences && Object.keys(occurrences).length > 0 && _orderedLabels.includes(type)) {
      occurrenceTypes.push(type);
    }
    return occurrenceTypes;
  }, []);
}
