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

import React from 'react';
import PropTypes from 'prop-types';
import {Button} from 'semantic-ui-react';
import {connect} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';
import {FilterBarController, FilterDropdownFactory} from '../../common/filters/FilterBar';

import RecurrenceForm from './filters/RecurrenceForm';
import DateForm from './filters/DateForm';
import TimeForm from './filters/TimeForm';

import {renderRecurrence} from '../../util';
import dateRenderer from './filters/DateRenderer';
import timeRenderer from './filters/TimeRenderer';
import {actions as filtersActions} from '../../common/filters';
import * as bookRoomSelectors from './selectors';


class BookingFilterBar extends React.Component {
    static propTypes = {
        dayBased: PropTypes.bool,
        filters: PropTypes.shape({
            recurrence: PropTypes.shape({
                number: PropTypes.number,
                type: PropTypes.string,
                interval: PropTypes.string
            }).isRequired,
            dates: PropTypes.shape({
                startDate: PropTypes.string,
                endDate: PropTypes.string
            }).isRequired,
            timeSlot: PropTypes.shape({
                startTime: PropTypes.string,
                endTime: PropTypes.string
            }),
        }).isRequired,
        actions: PropTypes.shape({
            setFilterParameter: PropTypes.func
        }).isRequired,
    };

    static defaultProps = {
        dayBased: false,
    };

    render() {
        const {
            dayBased,
            filters: {recurrence, dates, timeSlot},
            actions: {setFilterParameter},
        } = this.props;

        return (
            <Button.Group size="small">
                <Button icon="calendar alternate outline" as="div" disabled />
                <FilterBarController>
                    <Overridable id="BookingFilterBar.recurrence">
                        <FilterDropdownFactory name="recurrence"
                                               title={<Translate>Recurrence</Translate>}
                                               form={(fieldValues, setParentField) => (
                                                   <RecurrenceForm setParentField={setParentField} {...fieldValues} />
                                               )}
                                               setGlobalState={({type, number, interval}) => {
                                                   setFilterParameter('recurrence', {type, number, interval});
                                               }}
                                               initialValues={recurrence}
                                               defaults={{
                                                   type: 'single',
                                                   number: 1,
                                                   interval: 'week'
                                               }}
                                               renderValue={renderRecurrence} />
                    </Overridable>
                    <FilterDropdownFactory name="dates"
                                           title={<Translate>Date</Translate>}
                                           form={(fieldValues, setParentField) => (
                                               <DateForm setParentField={setParentField}
                                                         isRange={recurrence.type !== 'single'}
                                                         {...dates} />
                                           )}
                                           setGlobalState={setFilterParameter.bind(undefined, 'dates')}
                                           initialValues={dates}
                                           renderValue={dateRenderer} />
                    {!dayBased && (
                        <FilterDropdownFactory name="timeSlot"
                                               title={<Translate>Time</Translate>}
                                               form={(fieldValues, setParentField) => (
                                                   <TimeForm setParentField={setParentField}
                                                             {...fieldValues} />
                                               )}
                                               setGlobalState={setFilterParameter.bind(undefined, 'timeSlot')}
                                               initialValues={timeSlot}
                                               renderValue={timeRenderer} />
                    )}
                </FilterBarController>
            </Button.Group>
        );
    }
}

export default connect(
    state => ({
        filters: bookRoomSelectors.getFilters(state),
    }),
    dispatch => ({
        actions: {
            setFilterParameter: (param, value) => {
                dispatch(filtersActions.setFilterParameter('bookRoom', param, value));
            }
        }
    })
)(Overridable.component('BookingFilterBar', BookingFilterBar));
