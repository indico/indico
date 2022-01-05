// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {FORM_ERROR} from 'final-form';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field, Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';

import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {handleAxiosError} from '../../utils/axios';

import {handleSubmissionError} from './errors';
import {FinalUnloadPrompt} from './unload';

export function getChangedValues(data, form) {
  const fields = form.getRegisteredFields().filter(x => !x.includes('['));
  return _.fromPairs(
    fields.filter(name => form.getFieldState(name).dirty).map(name => [name, data[name]])
  );
}

export function getValuesForFields(data, form) {
  const fields = form.getRegisteredFields().filter(x => !x.includes('['));
  return _.fromPairs(fields.map(name => [name, data[name]]));
}

/**
 * Handle the error from an axios request, taking into account submission
 * errors that can be handled by final-form instead of showing the usual
 * error dialog for them.
 */
export function handleSubmitError(error, fieldErrorMap = {}) {
  if (_.get(error, 'response.status') === 422) {
    // if it's 422 we assume it's from webargs validation
    return handleSubmissionError(error, null, fieldErrorMap);
  } else if (_.get(error, 'response.status') === 418) {
    // this is an error that was expected, and will be handled by the app
    return {[FORM_ERROR]: error.response.data.message};
  } else {
    // anything else here is unexpected and triggers the usual error dialog
    const message = handleAxiosError(error, true);
    return {[FORM_ERROR]: message};
  }
}

/** Conditionally show content within a FinalForm depending on the value of another field */
export const FieldCondition = ({when, is, children}) => (
  <Field
    name={when}
    subscription={{value: true}}
    render={({input: {value}}) => (value === is ? children : null)}
  />
);

FieldCondition.propTypes = {
  when: PropTypes.string.isRequired,
  is: PropTypes.any,
  children: PropTypes.node.isRequired,
};

FieldCondition.defaultProps = {
  is: true,
};

/**
 * A FinalForm wrapping a SUI Modal and Form.
 * The modal is always open since it's supposed to be controlled from outside by
 * being only rendered when it should be visible - this ensures that no state sticks
 * around when the modal isn't open.
 */
export function FinalModalForm({
  id,
  onClose,
  onSubmit,
  initialValues,
  initialValuesEqual,
  size,
  header,
  children,
  extraActions,
  disabledUntilChange,
  unloadPrompt,
  unloadPromptRouter,
  alignTop,
  submitLabel,
  className,
  decorators,
  validate,
}) {
  const confirmingOnClose = dirty => () => {
    if (
      !dirty ||
      // eslint-disable-next-line no-alert
      confirm(Translate.string('Are you sure you want to close this dialog without saving?'))
    ) {
      onClose();
    }
  };

  return (
    <FinalForm
      onSubmit={onSubmit}
      subscription={{submitting: true, dirty: unloadPrompt}}
      initialValues={initialValues}
      initialValuesEqual={initialValuesEqual}
      decorators={decorators}
      validate={validate}
    >
      {fprops => (
        <Modal
          onClose={unloadPrompt ? confirmingOnClose(fprops.dirty) : onClose}
          size={size}
          closeIcon={!fprops.submitting}
          closeOnEscape={!fprops.submitting}
          closeOnDimmerClick={!fprops.submitting}
          centered={!alignTop}
          open
        >
          <Modal.Header>{header}</Modal.Header>
          <Modal.Content>
            {unloadPrompt && <FinalUnloadPrompt router={unloadPromptRouter} />}
            <Form
              id={`final-modal-form-${id}`}
              className={className}
              onSubmit={fprops.handleSubmit}
            >
              {_.isFunction(children) ? children(fprops) : children}
            </Form>
          </Modal.Content>
          <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
            {_.isFunction(extraActions) ? extraActions(fprops) : extraActions}
            <FinalSubmitButton
              form={`final-modal-form-${id}`}
              label={submitLabel || Translate.string('Submit')}
              disabledUntilChange={disabledUntilChange}
            />
            <Form.Field disabled={fprops.submitting}>
              <Button onClick={onClose} disabled={fprops.submitting}>
                <Translate>Cancel</Translate>
              </Button>
            </Form.Field>
          </Modal.Actions>
        </Modal>
      )}
    </FinalForm>
  );
}

FinalModalForm.propTypes = {
  /** An ID for the form that must be unique on the page (while rendered). */
  id: PropTypes.string.isRequired,
  /**
   * An async function invoked when submitting the form; it must return the error if
   * submission fails, or nothing in case of success.
   */
  onSubmit: PropTypes.func.isRequired,
  /**
   * A function that's invoked when closing the modal. It needs to result in this component
   * no longer being rendered.
   */
  onClose: PropTypes.func.isRequired,
  /**
   * An object containing the initial form values; it can be left `null` when there are no
   * initial values (e.g. a form used to create something new).
   */
  initialValues: PropTypes.object,
  /**
   * Custom equality check for initialValues (see react-final-form docs for details).
   */
  initialValuesEqual: PropTypes.func,
  /** Decorators to apply to the final-form, e.g. to use final-form-calculate. */
  decorators: PropTypes.array,
  /** Form-level validator to apply to the final-form. */
  validate: PropTypes.func,
  /** The size of the modal. */
  size: PropTypes.oneOf(['mini', 'tiny', 'small', 'large', 'fullscreen']),
  /** The header of the modal (typically a title). */
  header: PropTypes.node.isRequired,
  /** Whether the submit button should remain disabled as long as the form is in pristine state. */
  disabledUntilChange: PropTypes.bool,
  /**
   * Whether to ask the user to confirm when unloading the page or closing the dialog using
   * anything but the explicit cancel button.
   */
  unloadPrompt: PropTypes.bool,
  /** Enable react-router integration for the unload prompt. */
  unloadPromptRouter: PropTypes.bool,
  /**
   * Whether the form should be aligned to the top of the page. This is recommended if the height
   * changes while the modal is open to avoid it jumping around.
   */
  alignTop: PropTypes.bool,
  /** A custom label for the submit button. */
  submitLabel: PropTypes.string,
  /** Additional CSS classes to set on the SUI Form. */
  className: PropTypes.string,
  /**
   * The content of the form. This can be either final-form fields (`FinalInput` etc.) or
   * a callable which is called with the form's render properties ("fprops") in case the
   * content needs access to them.
   */
  children: PropTypes.oneOfType([PropTypes.func, PropTypes.node]).isRequired,
  /**
   * Additional actions (usually one or more Button elements wrapped in a `<Form.Field>`).
   * If you need access to the fprops e.g. to disable the buttons while the form is being
   * submitted, you may pass a callable here.
   */
  extraActions: PropTypes.oneOfType([PropTypes.func, PropTypes.node]),
};

FinalModalForm.defaultProps = {
  initialValues: null,
  initialValuesEqual: undefined,
  decorators: undefined,
  validate: undefined,
  size: 'tiny', // default to something reasonably small - let people explicitly go larger!
  disabledUntilChange: true,
  unloadPrompt: false,
  unloadPromptRouter: false,
  alignTop: false,
  submitLabel: null,
  className: null,
  extraActions: null,
};
