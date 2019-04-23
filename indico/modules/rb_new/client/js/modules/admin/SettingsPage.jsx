/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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
import React, {useEffect} from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Field, Form as FinalForm} from 'react-final-form';
import {Form, Header, Message, Placeholder} from 'semantic-ui-react';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {PrincipalListField} from 'indico/react/components';
import {
    formatters, getChangedValues, FieldCondition, ReduxFormField, ReduxCheckboxField, UnloadPrompt,
    validators as v
} from 'indico/react/forms';
import {useFavoriteUsers} from 'indico/react/hooks';
import * as adminActions from './actions';
import * as adminSelectors from './selectors';
import CategoryList from './CategoryList';

import './SettingsPage.module.scss';


const SettingsPage = props => {
    const {settingsLoaded, settings, actions: {fetchSettings, updateSettings}} = props;

    const favoriteUsersController = useFavoriteUsers();
    useEffect(() => {
        fetchSettings();
    }, [fetchSettings]);

    const handleSubmit = async (data, form) => {
        const changedValues = getChangedValues(data, form);
        const rv = await updateSettings(changedValues);
        if (rv.error) {
            return rv.error;
        }
    };

    if (!settingsLoaded) {
        return (
            <Placeholder>
                <Placeholder.Line />
                <Placeholder.Line />
                <Placeholder.Line />
                <Placeholder.Line />
                <Placeholder.Line />
            </Placeholder>
        );
    }

    return (
        <>
            <Header as="h2">
                <Translate>General Settings</Translate>
            </Header>
            <FinalForm onSubmit={handleSubmit}
                       initialValues={settings}
                       initialValuesEqual={_.isEqual}
                       subscription={{
                           submitting: true,
                           hasValidationErrors: true,
                           pristine: true,
                           dirty: true,
                           submitSucceeded: true,
                           dirtySinceLastSubmit: true,
                       }}>
                {fprops => (
                    <Form onSubmit={fprops.handleSubmit}
                          success={fprops.submitSucceeded && !fprops.dirtySinceLastSubmit}>
                        <UnloadPrompt active={fprops.dirty} />
                        <Message>
                            <Message.Header>
                                <Translate>
                                    Specify who has access to the room booking system.
                                </Translate>
                            </Message.Header>
                            <Form.Group widths="equal">
                                <Field name="authorized_principals" component={ReduxFormField}
                                       as={PrincipalListField} withGroups
                                       favoriteUsersController={favoriteUsersController}
                                       isEqual={(a, b) => _.isEqual(a.sort(), b.sort())}
                                       label={Translate.string('Authorized users')}>
                                    <p className="field-description">
                                        <Translate>
                                            Restrict access to the room booking system to these users/groups.
                                            If empty, all logged-in users have access.
                                        </Translate>
                                    </p>
                                </Field>
                                <Field name="admin_principals" component={ReduxFormField}
                                       as={PrincipalListField} withGroups
                                       favoriteUsersController={favoriteUsersController}
                                       isEqual={(a, b) => _.isEqual(a.sort(), b.sort())}
                                       label={Translate.string('Administrators')}>
                                    <p className="field-description">
                                        <Translate>
                                            Grant full room booking admin permissions to these users/groups.
                                        </Translate>
                                    </p>
                                </Field>
                            </Form.Group>
                        </Message>
                        <Field name="tileserver_url" component={ReduxFormField} as="input"
                               format={formatters.trim} formatOnBlur
                               label={Translate.string('Tileserver URL')}
                               parse={val => val || null}
                               validate={val => {
                                   if (!val) {
                                       return undefined;
                                   } else if (!val.match(/https?:\/\/.+/)) {
                                       return Translate.string('Please provide a valid URL');
                                   } else {
                                       const missing = ['{x}', '{y}', '{z}'].filter(x => !val.includes(x));
                                       if (missing.length) {
                                           return PluralTranslate.string(
                                               'Missing placeholder: {placeholders}',
                                               'Missing placeholders: {placeholders}',
                                               missing.length,
                                               {placeholders: missing.join(', ')}
                                           );
                                       }
                                   }
                               }}>
                            <p className="field-description">
                                <Translate>
                                    If you want to use the map, specify the URL to a tileserver covering the
                                    area in which your rooms are located.
                                </Translate>
                            </p>
                        </Field>
                        <Field name="booking_limit" component={ReduxFormField} as="input"
                               type="number"
                               min="1"
                               required
                               parse={value => (value ? +value : null)}
                               label={Translate.string('Max. booking length')}
                               validate={v.min(1)}>
                            <p className="field-description">
                                <Translate>The maximum length (in days) a booking may last.</Translate>
                            </p>
                        </Field>
                        <Field name="notifications_enabled" component={ReduxCheckboxField}
                               componentLabel={Translate.string('Send reminders for upcoming bookings')} />
                        <FieldCondition when="notifications_enabled">
                            <Message>
                                <Message.Header>
                                    <Translate>
                                        Specify how many days in advance booking reminders should be sent
                                    </Translate>
                                </Message.Header>
                                <Form.Group widths="equal">
                                    <Field name="notification_before_days" component={ReduxFormField}
                                           as="input"
                                           type="number"
                                           min="1"
                                           max="30"
                                           required
                                           parse={value => (value ? +value : null)}
                                           label={Translate.string('Single/Daily bookings')}
                                           validate={v.range(1, 30)} />
                                    <Field name="notification_before_days_weekly" component={ReduxFormField}
                                           as="input"
                                           type="number"
                                           min="1"
                                           max="30"
                                           required
                                           parse={value => (value ? +value : null)}
                                           label={Translate.string('Weekly bookings')}
                                           validate={v.range(1, 30)} />
                                    <Field name="notification_before_days_monthly" component={ReduxFormField}
                                           as="input"
                                           type="number"
                                           min="1"
                                           max="30"
                                           required
                                           parse={value => (value ? +value : null)}
                                           label={Translate.string('Monthly bookings')}
                                           validate={v.range(1, 30)} />
                                </Form.Group>
                            </Message>
                        </FieldCondition>
                        <Field name="end_notifications_enabled" component={ReduxCheckboxField}
                               componentLabel={Translate.string('Send reminders when bookings are about to end')} />
                        <FieldCondition when="end_notifications_enabled">
                            <Message>
                                <Message.Header>
                                    <Translate>
                                        Specify how many days before the end of a booking reminders should be sent
                                    </Translate>
                                </Message.Header>
                                <Form.Group widths="equal">
                                    <Field name="end_notification_daily" component={ReduxFormField}
                                           as="input"
                                           type="number"
                                           min="1"
                                           max="30"
                                           required
                                           parse={value => (value ? +value : null)}
                                           label={Translate.string('Daily bookings')}
                                           validate={v.range(1, 30)} />
                                    <Field name="end_notification_weekly" component={ReduxFormField}
                                           as="input"
                                           type="number"
                                           min="1"
                                           max="30"
                                           required
                                           parse={value => (value ? +value : null)}
                                           label={Translate.string('Weekly bookings')}
                                           validate={v.range(1, 30)} />
                                    <Field name="end_notification_monthly" component={ReduxFormField}
                                           as="input"
                                           type="number"
                                           min="1"
                                           max="30"
                                           required
                                           parse={value => (value ? +value : null)}
                                           label={Translate.string('Monthly bookings')}
                                           validate={v.range(1, 30)} />
                                </Form.Group>
                            </Message>
                        </FieldCondition>
                        <Field name="excluded_categories" component={ReduxFormField} as={CategoryList}
                               label={Translate.string('Disable booking during event creation')}>
                            <p className="field-description">
                                <Translate>
                                    Specify the IDs of categories for which booking a room during event creation
                                    will not be suggested.
                                </Translate>
                            </p>
                        </Field>
                        <Field name="grace_period"
                               component={ReduxFormField}
                               as="input"
                               type="number"
                               min="0"
                               max="24"
                               parse={value => (value !== '' ? +value : null)}
                               label={Translate.string('Grace period')}>
                            <p className="field-description">
                                <Translate>
                                    Usually booking a space in the past is not allowed. This setting will allow to
                                    book a room with a start date within a specified number of hours in the past.
                                    Leaving the field empty will allow any start date that is not in the past
                                    without restricting the start time as well.
                                </Translate>
                            </p>
                        </Field>
                        <Form.Button type="submit"
                                     disabled={(
                                         fprops.hasValidationErrors ||
                                         fprops.pristine ||
                                         fprops.submitting
                                     )}
                                     loading={fprops.submitting}
                                     primary
                                     content={Translate.string('Save')} />
                        <Message success>
                            <Translate>Settings have been saved.</Translate>
                        </Message>
                    </Form>
                )}
            </FinalForm>
        </>
    );
};

SettingsPage.propTypes = {
    settingsLoaded: PropTypes.bool.isRequired,
    settings: PropTypes.object.isRequired,
    actions: PropTypes.exact({
        fetchSettings: PropTypes.func.isRequired,
        updateSettings: PropTypes.func.isRequired,
    }).isRequired,
};

export default connect(
    state => ({
        settings: adminSelectors.getSettings(state),
        settingsLoaded: adminSelectors.hasSettingsLoaded(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchSettings: adminActions.fetchSettings,
            updateSettings: adminActions.updateSettings,
        }, dispatch),
    })
)(React.memo(SettingsPage));
