// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import allTemplatesURL from 'indico-url:receipts.all_templates';
import previewReceiptsURL from 'indico-url:receipts.receipts_preview';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {Button, Form, Grid, Header, Icon, Message, Popup, Segment} from 'semantic-ui-react';

import {
  formatters,
  FinalCheckbox,
  FinalDropdown,
  FinalField,
  FinalInput,
  FinalSubmitButton,
} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {snakifyKeys} from 'indico/utils/case';

import Previewer from '../templates/Previewer.jsx';

import {printReceipt} from './print.jsx';
import TemplateParameterEditor from './TemplateParameterEditor.jsx';

/**
 * This modal presents the user with a structured interface to download, e-mail or publish
 * receipts based on information from specific event registrations.
 */
export default function PrintReceiptsModal({onClose, registrationIds, eventId}) {
  const [generating, setGenerating] = useState(false);
  const [receipts, setReceipts] = useState([]);
  const [initialValues, setInitialValues] = useState({
    custom_fields: {},
    document_type: 'none',
    filename: 'document',
  });

  const {data, loading} = useIndicoAxios(allTemplatesURL({event_id: eventId}), {
    trigger: eventId,
    camelize: true,
  });
  const ready = !loading && !!data;

  const makeUpdateTemplateFields = form => templateId => {
    const {customFields, defaultFilename} = data.find(t => t.id === templateId);
    form.change(
      'custom_fields',
      customFields
        ? Object.assign({}, ...customFields.map(f => ({[f.name]: f.default || null})))
        : {}
    );
    form.change('filename', defaultFilename);
  };

  const getCustomFields = templateId =>
    ready && data.find(tpl => tpl.id === templateId)?.customFields;

  return (
    <FinalModalForm
      id="print-receipts"
      size="large"
      onSubmit={async values => {
        setGenerating(true);
        const result = await printReceipt(eventId, registrationIds, values);
        setGenerating(false);
        if (result && result.length > 0) {
          setReceipts(result);
          setInitialValues(values);
        }
      }}
      initialValues={initialValues}
      onClose={onClose}
      header={Translate.string('Generate Documents')}
      extraActions={
        <Button.Group style={{fontSize: 'inherit'}} primary>
          {[
            {
              icon: 'download',
              action: 'download',
              label: Translate.string('Download'),
              text: Translate.string('The document(s) will be downloaded immediately'),
            },
            {
              icon: 'mail',
              action: 'mail',
              label: Translate.string('E-mail'),
              text: Translate.string(
                'The document(s) will be e-mailed to the corresponding registrants'
              ),
            },
          ].map(({icon, action, label, text}) => (
            <Popup
              key={action}
              content={text}
              trigger={<Button disabled={receipts.length === 0} icon={icon} content={label} />}
            />
          ))}
        </Button.Group>
      }
      noSubmitButton
    >
      {fprops => (
        <>
          <Message color={receipts.length === 0 ? 'teal' : 'green'}>
            <Icon name="print" size="big" />
            {receipts.length === 0 ? (
              <PluralTranslate count={registrationIds.length}>
                <Singular>Generating document for a single registrant</Singular>
                <Plural>
                  Generating documents for{' '}
                  <Param
                    name="numberOfRegistrants"
                    value={registrationIds.length}
                    wrapper={<strong />}
                  />{' '}
                  registrants
                </Plural>
              </PluralTranslate>
            ) : (
              <PluralTranslate count={receipts.length}>
                <Singular>Successfully generated document for a single registrant</Singular>
                <Plural>
                  Successfully generated{' '}
                  <Param name="numberOfReceipts" value={receipts.length} wrapper={<strong />} />{' '}
                  documents
                </Plural>
              </PluralTranslate>
            )}
          </Message>
          <Grid columns={2} divided>
            <Grid.Column>
              <FinalDropdown
                name="template"
                loading={!ready}
                label={Translate.string('Document Template')}
                placeholder={Translate.string('Select a receipt template')}
                options={
                  ready ? data.map(({id, title}) => ({key: id, text: title, value: id})) : []
                }
                onChange={makeUpdateTemplateFields(fprops.form)}
                required
                selection
              />
              <Field name="template" subscription={{value: true}}>
                {({input: {value: template}}) => (
                  <FinalField
                    name="custom_fields"
                    component={TemplateParameterEditor}
                    customFields={template ? getCustomFields(template) : []}
                    title={Translate.string('Template Parameters')}
                  />
                )}
              </Field>
              <Field name="template" subscription={{value: true}}>
                {({input: {value: template}}) => (
                  <FinalInput
                    name="filename"
                    label={Translate.string('Filename')}
                    type="text"
                    componentLabel="-{n}.pdf"
                    labelPosition="right"
                    disabled={!template}
                    format={formatters.slugify}
                    formatOnBlur
                    required
                    fluid
                  />
                )}
              </Field>
              <FinalCheckbox
                name="publish"
                label={Translate.string('Publish document')}
                description={Translate.string(
                  'Make the resulting document(s) available on the registration page.'
                )}
                onChange={checked => {
                  if (!checked) {
                    fprops.form.change('notify_users', false);
                  }
                }}
              />
              <Field name="publish" subscription={{value: true}}>
                {({input: {value: publish}}) => (
                  <FinalCheckbox
                    name="notify_users"
                    disabled={!publish}
                    label={Translate.string('Notify registrant(s) via e-mail')}
                    description={Translate.string(
                      'Send an e-mail to the registrant(s) informing them that the document is available.'
                    )}
                  />
                )}
              </Field>
              <Form.Group style={{alignItems: 'center'}}>
                <Field name="publish" subscription={{value: true}}>
                  {({input: {value: publish}}) => (
                    <FinalSubmitButton
                      disabled={false || generating}
                      loading={generating}
                      label={
                        receipts.length === 0
                          ? publish
                            ? Translate.string('Generate and Publish')
                            : Translate.string('Generate')
                          : Translate.string('Re-generate')
                      }
                      icon="sync"
                      style={{width: '100%'}}
                      fluid
                    />
                  )}
                </Field>
                {receipts.length > 0 && <Icon name="check" color="green" size="large" />}
              </Form.Group>
            </Grid.Column>
            <Grid.Column>
              <Field name="template" subscription={{value: true}}>
                {({input: {value: templateId}}) =>
                  templateId ? (
                    <Field name="custom_fields" subscription={{value: true}}>
                      {({input: {value: customFields}}) => (
                        <Previewer
                          url={previewReceiptsURL(snakifyKeys({eventId, templateId}))}
                          data={snakifyKeys({customFields, registrationIds})}
                        />
                      )}
                    </Field>
                  ) : (
                    <Segment placeholder>
                      <Header icon>
                        <Icon name="eye" />
                        <Translate>Please select a template to preview it...</Translate>
                      </Header>
                    </Segment>
                  )
                }
              </Field>
            </Grid.Column>
          </Grid>
        </>
      )}
    </FinalModalForm>
  );
}

PrintReceiptsModal.propTypes = {
  onClose: PropTypes.func.isRequired,
  registrationIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  eventId: PropTypes.number.isRequired,
};
