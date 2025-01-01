// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import reportErrorURL from 'indico-url:core.report_error_api';

import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Icon, Message, Modal} from 'semantic-ui-react';

import {handleSubmissionError, FinalInput, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

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
  };

  static defaultProps = {
    errorData: undefined,
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
    const {
      errorData: {errorUUID},
    } = this.props;
    try {
      await indicoAxios.post(reportErrorURL({error_id: errorUUID}), {
        comment,
        email: email || undefined,
      });
    } catch (error) {
      return handleSubmissionError(error, Translate.string('Submitting your error report failed'));
    }
  };

  renderReportForm({handleSubmit, submitFailed, submitSucceeded, hasSubmitErrors, submitError}) {
    return (
      <Form onSubmit={handleSubmit} error={submitFailed} success={submitSucceeded}>
        {hasSubmitErrors && <Message error content={submitError} />}
        <FinalTextArea
          name="comment"
          label={Translate.string('Details')}
          autoFocus
          required
          description={
            <Translate>Please let us know what you were doing when the error showed up.</Translate>
          }
        />
        <FinalInput
          name="email"
          type="email"
          label={Translate.string('Email address')}
          description={
            <Translate>
              If you enter your email address we can contact you to follow-up on your error report.
            </Translate>
          }
        />
      </Form>
    );
  }

  renderReportActions({submitting, handleSubmit, hasValidationErrors, submitSucceeded}) {
    const {formVisible} = this.props;
    if (formVisible) {
      return (
        <Button
          type="submit"
          primary
          loading={submitting}
          disabled={submitting || hasValidationErrors || submitSucceeded}
          onClick={handleSubmit}
        >
          {submitSucceeded && <Icon name="checkmark" />}
          <Translate>Submit Report</Translate>
        </Button>
      );
    } else {
      return (
        <Button primary onClick={this.showReportForm}>
          <Translate>Report Error</Translate>
        </Button>
      );
    }
  }

  render() {
    const {errorData, remainingErrors, dialogVisible, formVisible} = this.props;
    if (!dialogVisible) {
      return null;
    }

    const {title, message, reportable} = errorData;

    const modal = fprops => (
      <Modal size="tiny" closeOnDimmerClick={false} closeOnEscape={false} open={dialogVisible}>
        <Modal.Content>
          <Message error icon>
            <Icon name="exclamation triangle" />
            <Message.Content>
              <Message.Header>{title}</Message.Header>
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
          {formVisible && !fprops.submitSucceeded && this.renderReportForm(fprops)}
          {fprops.submitSucceeded && (
            <Message success>
              <Translate>Thanks for your error report.</Translate>
            </Message>
          )}
        </Modal.Content>
        <Modal.Actions>
          {reportable && this.renderReportActions(fprops)}
          <Button
            onClick={() => {
              fprops.form.reset();
              this.clearError();
            }}
          >
            {remainingErrors ? (
              <Translate>Dismiss (show next error)</Translate>
            ) : (
              <Translate>Dismiss</Translate>
            )}
          </Button>
        </Modal.Actions>
      </Modal>
    );

    return (
      <FinalForm
        initialValues={{email: Indico.User.email}}
        onSubmit={this.submitReport}
        render={modal}
      />
    );
  }
}
