// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useState} from 'react';
import {Form as FinalForm, FormSpy} from 'react-final-form';
import {Accordion, Button, Form, Header, Message, Segment, Table} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';

import getFields from './fields';

import './FieldsDemo.module.scss';

function prettyPrintJson(obj) {
  return JSON.stringify(obj, null, 2);
}

interface FieldType {
  component: React.ElementType;
  initialValue: object | undefined;
  placeholder: string | undefined;
}

function FieldDemo({component: Component, initialValue, placeholder, ...extraOptions}: FieldType) {
  const [output, setOutput] = useState(null);
  return (
    <FinalForm
      onSubmit={({field}) => setOutput(field)}
      initialValuesEqual={_.isEqual}
      initialValues={{
        field: initialValue,
        label: 'Field',
        placeholder,
        options: prettyPrintJson(extraOptions),
      }}
      subscription={{
        pristine: true,
        submitSucceeded: true,
        validating: true,
        hasValidationErrors: true,
        errors: true,
      }}
    >
      {({
        handleSubmit,
        form,
        pristine,
        submitSucceeded,
        validating,
        hasValidationErrors,
        errors,
      }) => (
        <Form onSubmit={handleSubmit}>
          <FormSpy subscription={{values: true}}>
            {({
              values: {
                label,
                description,
                disabled,
                required,
                placeholder: placeholderValue,
                options,
              },
            }) => {
              try {
                options = JSON.parse(options);
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
              return (
                <Segment raised>
                  <Component
                    name="field"
                    label={label}
                    description={description}
                    disabled={disabled}
                    required={required}
                    placeholder={placeholderValue}
                    {...options}
                  />
                </Segment>
              );
            }}
          </FormSpy>
          <FieldControls
            {...{
              pristine,
              validating,
              hasValidationErrors,
              submitSucceeded,
              errors,
              placeholder,
              extraOptions,
            }}
          />
          <div styleName="form-actions">
            <Button type="button" onClick={() => form.reset()} disabled={pristine}>
              Clear
            </Button>
            <FinalSubmitButton label="Submit" disabledUntilChange={false} />
          </div>
          {submitSucceeded && (
            <>
              <Header as="h4" dividing>
                Output
              </Header>
              <pre styleName="submitted-value">{prettyPrintJson(output)}</pre>
            </>
          )}
        </Form>
      )}
    </FinalForm>
  );
}

interface FieldControlsPropTypes {
  pristine: boolean;
  validating: boolean;
  hasValidationErrors: boolean;
  submitSucceeded: boolean;
  errors: object;
  placeholder: string | undefined;
  extraOptions: object;
}

function FieldControls({
  pristine,
  submitSucceeded,
  validating,
  hasValidationErrors,
  errors,
  placeholder,
  extraOptions,
}: FieldControlsPropTypes) {
  const formInfo = (
    <Table definition>
      <Table.Body>
        <Table.Row>
          <Table.Cell>Pristine</Table.Cell>
          <Table.Cell>{String(pristine)}</Table.Cell>
        </Table.Row>
        <Table.Row positive={submitSucceeded}>
          <Table.Cell>Submit succeeded</Table.Cell>
          <Table.Cell>{String(submitSucceeded)}</Table.Cell>
        </Table.Row>
        <Table.Row>
          <Table.Cell>Validating</Table.Cell>
          <Table.Cell>{String(validating)}</Table.Cell>
        </Table.Row>
        <Table.Row negative={hasValidationErrors}>
          <Table.Cell>Has validation errors</Table.Cell>
          <Table.Cell>{String(hasValidationErrors)}</Table.Cell>
        </Table.Row>
        <Table.Row negative={hasValidationErrors}>
          <Table.Cell>Errors</Table.Cell>
          <Table.Cell>{prettyPrintJson(errors)}</Table.Cell>
        </Table.Row>
      </Table.Body>
    </Table>
  );

  const rows = prettyPrintJson(extraOptions).split('\n').length;
  const formOptions = (
    <>
      <Header as="h4" dividing>
        Field options
      </Header>
      <Form.Group widths="equal">
        <FinalInput name="label" label="Label" />
        <FinalTextArea name="description" label="Description" rows={1} />
      </Form.Group>
      {placeholder && <FinalInput name="placeholder" label="Placeholder" />}
      <FinalCheckbox name="disabled" label="Disabled" />
      <FinalCheckbox name="required" label="Required" />
      {Object.keys(extraOptions).length > 0 && (
        <FinalTextArea
          name="options"
          styleName="extra-options-field"
          label="Other options"
          nullIfEmpty
          rows={rows}
          spellCheck="false"
        />
      )}
    </>
  );

  return (
    <Accordion
      panels={[
        {key: 'formInfo', title: 'Form state', content: {content: formInfo}},
        {key: 'formOptions', title: 'Field options', content: {content: formOptions}},
      ]}
      exclusive={false}
      styled
      fluid
    />
  );
}

export default function FieldsDemo() {
  interface FieldDefinitionType extends FieldType {
    title: string;
  }

  return (
    <Accordion
      panels={_.sortBy(getFields(), 'title').map(({title, ...field}: FieldDefinitionType) => ({
        key: title,
        title,
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
