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
import {Button, Form, Icon, Message, Modal, TextArea} from 'semantic-ui-react';
import {Field, SubmissionError} from 'redux-form';
import reportErrorURL from 'indico-url:core.report_error_api';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {fieldRequired, ReduxFormField} from './util';


export default class ErrorDialog extends React.Component {
    static propTypes = {
        errorData: PropTypes.shape({
            title: PropTypes.string.isRequired,
            message: PropTypes.string.isRequired,
            reportable: PropTypes.bool.isRequired,
            errorUUID: PropTypes.string,
        }),
        remainingErrors: PropTypes.number.isRequired,
        dialogVisible: PropTypes.bool.isRequired,
        formVisible: PropTypes.bool.isRequired,
        clearError: PropTypes.func.isRequired,
        showReportForm: PropTypes.func.isRequired,
        // redux-form stuff
        error: PropTypes.string,
        submitting: PropTypes.bool.isRequired,
        invalid: PropTypes.bool.isRequired,
        pristine: PropTypes.bool.isRequired,
        submitSucceeded: PropTypes.bool.isRequired,
        submitFailed: PropTypes.bool.isRequired,
        handleSubmit: PropTypes.func.isRequired,
    };

    static defaultProps = {
        errorData: undefined,
        error: undefined,
    };

    clearError = () => {
        const {clearError} = this.props;
        clearError();
    };

    showReportForm = () => {
        const {showReportForm} = this.props;
        showReportForm();
    };

    submitReport = async ({email, comment}) => {
        const {errorData: {errorUUID}} = this.props;
        try {
            await indicoAxios.post(reportErrorURL({error_id: errorUUID}), {
                comment,
                email: email || undefined
            });
        } catch (error) {
            throw new SubmissionError({_error: Translate.string('Submitting your error report failed')});
        }
    };

    renderReportForm() {
        const {handleSubmit, submitFailed, submitSucceeded, error} = this.props;
        return (
            <Form onSubmit={handleSubmit(this.submitReport)} error={submitFailed} success={submitSucceeded}>
                {error && <Message error content={error} />}
                <Field name="comment" component={ReduxFormField} as={TextArea}
                       label={Translate.string('Details')} autoFocus required
                       validate={fieldRequired}>
                    <p style={{fontStyle: 'italic', fontSize: '0.9em', color: '#999'}}>
                        <Translate>
                            Please let us know what you were doing when the error showed up.
                        </Translate>
                    </p>
                </Field>
                <Field name="email" component={ReduxFormField} as="input" type="email"
                       label={Translate.string('Email address')}>
                    <p style={{fontStyle: 'italic', fontSize: '0.9em', color: '#999'}}>
                        <Translate>
                            If you enter your email address we can contact you to follow-up
                            on your error report.
                        </Translate>
                    </p>
                </Field>
            </Form>
        );
    }

    renderReportActions() {
        const {submitting, handleSubmit, invalid, pristine, submitSucceeded, formVisible} = this.props;
        if (formVisible) {
            return (
                <Button type="submit" primary
                        loading={submitting} disabled={submitting || invalid || pristine || submitSucceeded}
                        onClick={handleSubmit(this.submitReport)}>
                    {submitSucceeded && <Icon name="checkmark" />}
                    <Translate>Submit Report</Translate>
                </Button>
            );
        } else {
            return <Button primary onClick={this.showReportForm}><Translate>Report Error</Translate></Button>;
        }
    }

    render() {
        const {errorData, remainingErrors, dialogVisible, formVisible, submitSucceeded} = this.props;
        if (!dialogVisible) {
            return null;
        }

        const {title, message, reportable} = errorData;

        return (
            <Modal size="tiny" dimmer="blurring" open={dialogVisible} onClose={this.clearError}>
                <Modal.Content>
                    <Message error icon>
                        <Icon name="exclamation triangle" />
                        <Message.Content>
                            <Message.Header>
                                {title}
                            </Message.Header>
                            {message}
                        </Message.Content>
                    </Message>
                    {reportable && !formVisible && (
                        <p>
                            <Translate>
                                Please report this error to us if it persists after reloading the page.
                            </Translate>
                        </p>
                    )}
                    {formVisible && !submitSucceeded && this.renderReportForm()}
                    {submitSucceeded && (
                        <Message success><Translate>Thanks for your error report.</Translate></Message>
                    )}
                </Modal.Content>
                <Modal.Actions>
                    {reportable && this.renderReportActions()}
                    <Button onClick={this.clearError}>
                        {!remainingErrors
                            ? <Translate>Dismiss</Translate>
                            : (
                                <PluralTranslate count={remainingErrors}>
                                    <Singular>
                                        Dismiss (one more error)
                                    </Singular>
                                    <Plural>
                                        Dismiss (<Param name="count" value={remainingErrors} /> more errors)
                                    </Plural>
                                </PluralTranslate>
                            )
                        }
                    </Button>
                </Modal.Actions>
            </Modal>
        );
    }
}
