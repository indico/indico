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
import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Form, Input, Segment, Select, TextArea} from 'semantic-ui-react';
import {Field} from 'react-final-form';
import {START_DATE} from 'react-dates/constants';

import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import {ReduxFormField, ReduxRadioField, formatters, validators as v} from 'indico/react/forms';
import {SingleDatePicker, DatePeriodField} from 'indico/react/components';
import {serializeDate, serializeTime, toMoment} from 'indico/utils/date';
import {Overridable} from 'indico/react/util';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import TimeRangePicker from '../../components/TimeRangePicker';
import {selectors as userSelectors} from '../user';
import {sanitizeRecurrence} from '../../util';

import './BookingEditForm.module.scss';


class BookingEditForm extends React.Component {
    static propTypes = {
        user: PropTypes.object.isRequired,
        favoriteUsers: PropTypes.array.isRequired,
        booking: PropTypes.object.isRequired,
        formProps: PropTypes.object.isRequired,
        onBookingPeriodChange: PropTypes.func,
        hideOptions: PropTypes.objectOf(PropTypes.bool),
    };

    static defaultProps = {
        onBookingPeriodChange: () => {},
        hideOptions: {},
    };

    recurrenceTypeChanged = (newType) => {
        const {
            booking: {startDt},
            onBookingPeriodChange,
            formProps: {form, values: {recurrence, dates, timeSlot}}
        } = this.props;
        const filters = {dates, recurrence: {...recurrence, type: newType}};
        const today = moment();

        if (['daily', 'every'].includes(newType) && today.isAfter(startDt, 'day')) {
            dates.startDate = serializeDate(startDt);
        } else if (newType === 'single' && today.isAfter(startDt, 'day')) {
            dates.startDate = serializeDate(today);
        }

        sanitizeRecurrence(filters);
        form.change('recurrence', filters.recurrence);
        form.change('dates', filters.dates);

        onBookingPeriodChange(filters.dates, timeSlot, filters.recurrence);
    };

    renderRecurrenceNumber = ({input, onChange, ...fieldProps}) => {
        return (
            <ReduxFormField {...fieldProps}
                            input={input}
                            onChange={(__, {value}) => {
                                input.onChange(value);
                                onChange(value);
                            }}
                            type="number"
                            min="1"
                            max="99"
                            step="1" />
        );
    };


    renderIntervalDropdown = ({input, onChange, ...fieldProps}) => {
        const {formProps: {values: {recurrence: {number}}}} = this.props;

        const recurrenceOptions = [
            {text: PluralTranslate.string('Week', 'Weeks', number), value: 'week'},
            {text: PluralTranslate.string('Month', 'Months', number), value: 'month'}
        ];

        return (
            <ReduxFormField {...fieldProps}
                            input={input}
                            as={Select}
                            options={recurrenceOptions}
                            onChange={(__, {value}) => {
                                input.onChange(value);
                                onChange(value);
                            }} />

        );
    };

    renderDateForm = ({input, isSingleBooking, onChange, ...fieldProps}) => {
        const {booking: {startDt: originalStartDt, endDt: originalEndDt}} = this.props;
        const {value: {startDate, endDate}} = input;
        const component = isSingleBooking ? SingleDatePicker : DatePeriodField;
        const today = moment();
        const props = isSingleBooking ? {
            onDateChange: (date) => {
                const dates = {startDate: serializeDate(date), endDate: null};
                input.onChange(dates);
                onChange(dates);
            },
            date: toMoment(startDate, 'YYYY-MM-DD'),
            disabled: toMoment(originalEndDt, 'YYYY-MM-DD').isBefore(today, 'day'),
        } : {
            onChange: (dates) => {
                input.onChange(dates);
                onChange(dates);
            },
            dates: {
                startDate: toMoment(startDate, 'YYYY-MM-DD'),
                endDate: toMoment(endDate, 'YYYY-MM-DD')
            },
            disabled: today.isAfter(originalStartDt, 'day') && today.isAfter(originalEndDt, 'day'),
            disabledDateFields: today.isAfter(startDate, 'day') ? START_DATE : null,
        };

        const disabledDate = (dt) => {
            if (today.isSameOrBefore(originalStartDt, 'day') || today.isAfter(originalStartDt, 'day')) {
                return !dt.isSameOrAfter(today, 'day');
            }

            return !dt.isSameOrAfter(originalStartDt, 'day');
        };

        return (
            <ReduxFormField {...fieldProps}
                            {...props}
                            disabledDate={disabledDate}
                            input={input}
                            as={component} />
        );
    };

    renderTimeForm = ({input, onChange, ...fieldProps}) => {
        const {value: {startTime, endTime}} = input;
        const {booking: {startDt, endDt}} = this.props;
        const today = moment();
        const disabled = today.isAfter(startDt, 'day') && (endDt && today.isAfter(endDt, 'day'));

        return (
            <ReduxFormField {...fieldProps}
                            disabled={disabled}
                            input={input}
                            as={TimeRangePicker}
                            startTime={toMoment(startTime, 'HH:mm')}
                            endTime={toMoment(endTime, 'HH:mm')}
                            onChange={(start, end) => {
                                const newTimeSlot = {
                                    startTime: serializeTime(start),
                                    endTime: serializeTime(end),
                                };

                                input.onChange(newTimeSlot);
                                onChange(newTimeSlot);
                            }} />
        );
    };

    renderPrincipalSearchField = ({input, currentUser, showCurrentUserPlaceholder, ...fieldProps}) => {
        const {favoriteUsers} = this.props;
        if (showCurrentUserPlaceholder && !_.isEmpty(currentUser)) {
            fieldProps.placeholder = currentUser.fullName;
        }
        return (
            <ReduxFormField {...fieldProps}
                            input={{...input, value: input.value || null}}
                            as={PrincipalSearchField}
                            onChange={(value) => input.onChange(value)}
                            favoriteUsers={favoriteUsers} />
        );
    };

    render() {
        const {
            user: sessionUser,
            booking: {bookedForUser, startDt, endDt},
            onBookingPeriodChange,
            formProps,
            hideOptions,
        } = this.props;
        const {
            values: {dates, recurrence, timeSlot, usage, user},
            submitting, submitSucceeded, form, handleSubmit
        } = formProps;
        const bookedByCurrentUser = sessionUser.id === bookedForUser.id;
        const today = moment();
        const bookingFinished = today.isAfter(startDt, 'day') && (endDt && today.isAfter(endDt, 'day'));

        return (
            <Form id="booking-edit-form" styleName="booking-edit-form" onSubmit={handleSubmit}>
                <Segment>
                    <Form.Group inline>
                        {!hideOptions.single && (
                            <Field name="recurrence.type"
                                   component={ReduxRadioField}
                                   componentLabel={Translate.string('Single booking')}
                                   radioValue="single"
                                   disabled={submitting || submitSucceeded || bookingFinished}
                                   onClick={() => this.recurrenceTypeChanged('single')} />
                        )}
                        {!hideOptions.daily && (
                            <Field name="recurrence.type"
                                   component={ReduxRadioField}
                                   componentLabel={Translate.string('Daily booking')}
                                   radioValue="daily"
                                   disabled={submitting || submitSucceeded || bookingFinished}
                                   onClick={() => this.recurrenceTypeChanged('daily')} />
                        )}
                        {!hideOptions.recurring && (
                            <Field name="recurrence.type"
                                   component={ReduxRadioField}
                                   componentLabel={Translate.string('Recurring booking')}
                                   radioValue="every"
                                   disabled={submitting || submitSucceeded || bookingFinished}
                                   onClick={() => this.recurrenceTypeChanged('every')} />
                        )}
                    </Form.Group>
                    {recurrence.type === 'every' && (
                        <Form.Group inline>
                            <label>
                                <Translate>Every</Translate>
                            </label>
                            <Field name="recurrence.number"
                                   as={Input}
                                   validate={v.min(1)}
                                   disabled={submitting || submitSucceeded}
                                   onChange={(newNumber) => {
                                       if (+newNumber > 0) {
                                           const newRecurrence = {...recurrence, number: newNumber};
                                           onBookingPeriodChange(dates, timeSlot, newRecurrence);
                                       }
                                   }}
                                   render={this.renderRecurrenceNumber} />
                            <Field name="recurrence.interval"
                                   disabled={submitting || submitSucceeded}
                                   onChange={(newInterval) => {
                                       const newRecurrence = {...recurrence, interval: newInterval};
                                       onBookingPeriodChange(dates, timeSlot, newRecurrence);
                                   }}
                                   render={this.renderIntervalDropdown} />
                        </Form.Group>
                    )}
                    <Field name="dates"
                           isSingleBooking={recurrence.type === 'single'}
                           onChange={(newDates) => onBookingPeriodChange(newDates, timeSlot, recurrence)}
                           disabled={submitting || submitSucceeded}
                           isEqual={_.isEqual}
                           render={this.renderDateForm} />
                    {!hideOptions.timeSlot && (
                        <Field name="timeSlot"
                               onChange={(newTimeSlot) => onBookingPeriodChange(dates, newTimeSlot, recurrence)}
                               disabled={submitting || submitSucceeded}
                               isEqual={_.isEqual}
                               render={this.renderTimeForm} />
                    )}
                </Segment>
                <Segment color="blue" inverted>
                    <Form.Group>
                        <Field name="usage"
                               radioValue="myself"
                               component={ReduxRadioField}
                               onClick={() => form.change('user', {...sessionUser, isGroup: false})}
                               componentLabel={Translate.string("I'll be using it myself")}
                               disabled={submitting || submitSucceeded}
                               checked={usage === 'myself'} />
                        <Field name="usage"
                               radioValue="someone"
                               component={ReduxRadioField}
                               onClick={() => form.change('user', bookedByCurrentUser ? null : bookedForUser)}
                               componentLabel={Translate.string("I'm booking it for someone else")}
                               disabled={submitting || submitSucceeded}
                               checked={usage === 'someone'} />
                    </Form.Group>
                    <Field name="user"
                           render={this.renderPrincipalSearchField}
                           required={usage === 'someone'}
                           currentUser={user}
                           disabled={usage === 'myself' || (submitting || submitSucceeded)}
                           isEqual={(a, b) => a && b && a.identifier === b.identifier}
                           validate={v.required}
                           showCurrentUserPlaceholder={usage === 'myself'} />
                    <Field name="reason"
                           component={ReduxFormField}
                           as={TextArea}
                           format={formatters.trim}
                           placeholder={Translate.string('Reason for booking')}
                           validate={v.required}
                           disabled={submitting || submitSucceeded}
                           formatOnBlur />
                </Segment>
            </Form>
        );
    }
}

export default connect(
    (state) => ({
        user: userSelectors.getUserInfo(state),
        favoriteUsers: userSelectors.getFavoriteUsers(state),
    }),
)(Overridable.component('BookingEditForm', BookingEditForm));
