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
import {push} from 'connected-react-router';
import moment from 'moment';
import {Popup} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import React from 'react';
import {serializeDate} from 'indico/utils/date';
import {PluralTranslate, Translate, Singular, Plural, Param} from 'indico/react/i18n';


export function preProcessParameters(params, rules) {
    return _pruneNullLeaves(
        Object.assign(...Object.entries(rules)
            .map(([k, rule]) => {
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
            }))
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
    const {dates: {endDate, startDate}, recurrence: {type, interval, number}} = filters;

    if (type === 'single' && endDate) {
        filters.dates = {...filters.dates, endDate: null};
    } else if (type !== 'single' && startDate && !endDate) {
        // if there's a start date already set, let's set a sensible
        // default for the end date
        filters.dates = {...filters.dates, endDate: calculateDefaultEndDate(startDate, type, number, interval)};
    }
}

function _pruneNullLeaves(obj) {
    if (!Object.entries(obj).length) {
        return {};
    }

    return Object.assign(...Object.entries(obj).map(([k, v]) => {
        if (v === null) {
            return {};
        } else if (Array.isArray(v)) {
            return {[k]: v.filter(e => e !== null)};
        } else if (typeof v === 'object') {
            return {[k]: _pruneNullLeaves(v)};
        } else {
            return {[k]: v};
        }
    }));
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
        }
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
        }
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
        }
    };
}

export function isDateWithinRange(date, dateRange, _toMoment) {
    return date && dateRange.filter((dt) => _toMoment(dt).isSame(date, 'day')).length !== 0;
}


export function PopupParam({content, children}) {
    const trigger = <span>{children}</span>;
    return <Popup trigger={trigger} content={content} />;
}

PopupParam.propTypes = {
    content: PropTypes.object.isRequired,
    children: PropTypes.object,
};

PopupParam.defaultProps = {
    children: null,
};

export function renderRecurrence({type, number, interval}) {
    if (!type) {
        return null;
    }
    if (type === 'single') {
        return <Translate>Once</Translate>;
    } else if (type === 'daily') {
        return <Translate>Daily</Translate>;
    } else if (interval === 'week') {
        return (
            <PluralTranslate count={number}>
                <Singular>
                    Weekly
                </Singular>
                <Plural>
                    Every <Param name="number" value={number} /> weeks
                </Plural>
            </PluralTranslate>
        );
    } else {
        return (
            <PluralTranslate count={number}>
                <Singular>
                    Monthly
                </Singular>
                <Plural>
                    Every <Param name="number" value={number} /> months
                </Plural>
            </PluralTranslate>
        );
    }
}

export function getRecurrenceInfo(repetition) {
    const [repeatFrequency, repeatInterval] = repetition;
    let type = 'single';
    let number = '1';
    let interval = 'week';
    if (repeatFrequency === 1) {
        type = 'daily';
    } else if (repeatFrequency === 2) {
        type = 'every';
        interval = 'week';
        number = repeatInterval;
    } else if (repeatFrequency === 3) {
        type = 'every';
        interval = 'month';
        number = repeatInterval;
    }
    return {type, number, interval};
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

const _legendLabels = {
    candidates:
        {label: Translate.string('Available'), style: 'available'},
    bookings:
        {label: Translate.string('Booking'), style: 'booking'},
    preBookings:
        {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
    conflicts:
        {label: Translate.string('Conflict'), style: 'conflict'},
    preConflicts:
        {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
    conflictingCandidates:
        {label: Translate.string('Invalid occurrence'), style: 'conflicting-candidate'},
    other:
        {label: Translate.string('Other booking'), style: 'other'},
    rejections:
        {label: Translate.string('Rejection'), style: 'rejection'},
    cancellations:
        {label: Translate.string('Cancellation'), style: 'cancellation'},
    pendingCancellations:
        {label: Translate.string('Pending cancellation'), style: 'pending-cancellation'},
    blockings:
        {label: Translate.string('Blocking'), style: 'blocking'},
    overridableBlockings:
        {label: Translate.string('Blocking (allowed)'), style: 'overridable-blocking'},
    nonbookablePeriods:
        {label: Translate.string('Not bookable'), style: 'unbookable'},
    unbookableHours:
        {label: Translate.string('Not bookable'), style: 'unbookable'}
};

const _orderedLabels = [
    'candidates',
    'bookings',
    'preBookings',
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

export function transformToLegendLabels(occurrenceTypes) {
    return _orderedLabels.reduce((legend, type) => {
        const label = _legendLabels[type];
        if (occurrenceTypes.includes(type) && !legend.some(legendLabel => legendLabel.style === label.style)) {
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
