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
import React from 'react';
import {push} from 'connected-react-router';
import moment from 'moment';
import {Dimmer} from 'semantic-ui-react';
import {Preloader} from 'indico/react/util';
import {serializeDate} from 'indico/utils/date';

import {selectors as roomsSelectors} from './common/rooms';


export function parseSearchBarText(queryText) {
    const resultMap = {bldg: 'building', floor: 'floor'};
    const result = {text: null, building: null, floor: null};
    if (!queryText) {
        return result;
    }

    const parts = queryText.split(/\s+/).filter(x => !!x);
    const textParts = [];
    for (const item of parts) {
        const [filter, value] = item.split(':');
        if (value && resultMap.hasOwnProperty(filter)) {
            result[resultMap[filter]] = value;
        } else if (item) {
            textParts.push(item);
        }
    }

    result.text = textParts.join(' ').trim() || null;
    return result;
}

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

export const roomPreloader = (componentFunc, action) => {
    // eslint-disable-next-line react/display-name, react/prop-types
    return ({match: {params: {roomId}}}) => (
        <Preloader checkCached={state => roomsSelectors.hasDetails(state, {roomId})}
                   action={() => action(roomId)}
                   dimmer={<Dimmer page />}>
            {() => componentFunc(roomId)}
        </Preloader>
    );
};

export function boolStateField(name) {
    return {
        serialize: state => _.get(state, name) || null,
        parse: (value, state) => {
            _.set(state, name, value);
        }
    };
}

export function isDateWithinRange(date, dateRange, _toMoment) {
    return date && dateRange.filter((dt) => _toMoment(dt).isSame(date, 'day')).length !== 0;
}
