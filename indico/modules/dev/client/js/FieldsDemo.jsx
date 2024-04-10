// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm, FormSpy} from 'react-final-form';
import {
  Accordion,
  Button,
  Form,
  Header,
  Icon,
  Message,
  Rail,
  Segment,
  Table,
} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';

import getFields from './fields';

import './FieldsDemo.module.scss';

function FieldDemo({title, component: Component, initialValue, ...extraOptions}) {
  const [showOptions, setShowOptions] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [output, setOutput] = useState(null);
  return (
    <FinalForm
      onSubmit={({field}) => setOutput(field)}
      initialValuesEqual={_.isEqual}
      initialValues={{
        field: initialValue,
        options: JSON.stringify(extraOptions, null, 2),
        label: 'Field',
      }}
      subscription={{
        validating: true,
        hasValidationErrors: true,
        pristine: true,
        submitSucceeded: true,
      }}
    >
      {({handleSubmit, form, validating, hasValidationErrors, pristine, submitSucceeded}) => (
        <Form onSubmit={handleSubmit}>
          {showOptions && (
            <Rail position="left" attached>
              <Segment>
                <Header as="h4" dividing>
                  Field options
                </Header>
                <FinalInput name="label" label="Label" />
                <FinalCheckbox name="disabled" label="Disabled" />
                <FinalCheckbox name="required" label="Required" />
                {Object.keys(extraOptions).length > 0 && (
                  <FinalTextArea
                    name="options"
                    styleName="extra-options-field"
                    label="Other options"
                    nullIfEmpty
                  />
                )}
              </Segment>
            </Rail>
          )}
          {showInfo && (
            <Rail position="right" attached>
              <Segment>
                <Header as="h4" dividing>
                  Form info
                </Header>
                <Table definition>
                  <Table.Body>
                    <Table.Row>
                      <Table.Cell>Validating</Table.Cell>
                      <Table.Cell>{String(validating)}</Table.Cell>
                    </Table.Row>
                    <Table.Row negative={hasValidationErrors}>
                      <Table.Cell>Has validation errors</Table.Cell>
                      <Table.Cell>{String(hasValidationErrors)}</Table.Cell>
                    </Table.Row>
                    <Table.Row>
                      <Table.Cell>Pristine</Table.Cell>
                      <Table.Cell>{String(pristine)}</Table.Cell>
                    </Table.Row>
                    <Table.Row positive={submitSucceeded}>
                      <Table.Cell>Submit succeeded</Table.Cell>
                      <Table.Cell>{String(submitSucceeded)}</Table.Cell>
                    </Table.Row>
                  </Table.Body>
                </Table>
              </Segment>
            </Rail>
          )}
          <FormSpy subscription={{values: true}}>
            {({values: {label, disabled, required, options}}) => {
              try {
                return (
                  <Segment raised>
                    <Component
                      name="field"
                      label={label}
                      disabled={disabled}
                      required={required}
                      {...JSON.parse(options)}
                    />
                  </Segment>
                );
              } catch {
                return (
                  <Message
                    icon="warning sign"
                    header="Invalid options"
                    content="The extra options must be a valid JSON object."
                    error
                    visible
                  />
                );
              }
            }}
          </FormSpy>
          <Form.Group styleName="form-actions">
            <Button type="button" onClick={() => form.reset()} disabled={pristine}>
              Clear
            </Button>
            <FinalSubmitButton label="Submit" disabledUntilChange={false} />
          </Form.Group>
          <div styleName="actions">
            <Icon
              name="setting"
              title="Show field options"
              color="blue"
              onClick={() => setShowOptions(!showOptions)}
              link
            />
            <Icon
              name="info circle"
              title="Show form info"
              color="blue"
              onClick={() => setShowInfo(!showInfo)}
              link
            />
          </div>
          {submitSucceeded && (
            <>
              <Header as="h4" dividing>
                Output
              </Header>
              <pre>{JSON.stringify(output, null, 2)}</pre>
            </>
          )}
        </Form>
      )}
    </FinalForm>
  );
}

FieldDemo.propTypes = {
  title: PropTypes.string.isRequired,
  component: PropTypes.elementType.isRequired,
  initialValue: PropTypes.any,
};

FieldDemo.defaultProps = {
  initialValue: null,
};

export default function FieldsDemo() {
  return (
    <Accordion
      panels={_.sortBy(getFields(), 'title').map(field => ({
        key: field.title,
        title: field.title,
        content: {
          content: <FieldDemo {...field} />,
        },
      }))}
      exclusive={false}
      styled
      fluid
    />
  );
}
