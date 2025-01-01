// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import allTemplatesURL from 'indico-url:receipts.all_templates';
import eventImagesURL from 'indico-url:receipts.images';
import exportReceiptsURL from 'indico-url:receipts.receipts_export';
import previewReceiptsURL from 'indico-url:receipts.receipts_preview';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Field, FormSpy} from 'react-final-form';
import {Button, Dropdown, Form, Grid, Header, Icon, Message, Segment} from 'semantic-ui-react';

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
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {downloadBlob} from 'indico/utils/browser';
import {snakifyKeys} from 'indico/utils/case';

import Previewer from '../templates/Previewer';

import {printReceipt} from './print';
import TemplateParameterEditor, {getDefaultFieldValue} from './TemplateParameterEditor';

const makeSubmitLabel = ({publish, notify_users: notifyUsers}, numRegistrants) => {
  if (publish) {
    return notifyUsers
      ? PluralTranslate.string(
          'Publish and send to registrant',
          'Publish and send to registrants',
          numRegistrants
        )
      : PluralTranslate.string(
          'Save and publish to registration',
          'Save and publish to registrations',
          numRegistrants
        );
  }
  return notifyUsers
    ? PluralTranslate.string(
        'Save and send to registrant',
        'Save and send to registrants',
        numRegistrants
      )
    : PluralTranslate.string('Save to registration', 'Save to registrations', numRegistrants);
};

const downloadOptions = [
  {
    key: 'pdf',
    value: 'pdf',
    text: Translate.string('as a single PDF document'),
  },
  {
    key: 'zip',
    value: 'zip',
    text: Translate.string('as a ZIP archive'),
  },
];

const archiveFilename = {
  pdf: 'documents.pdf',
  zip: 'documents.zip',
};

/**
 * This modal presents the user with a structured interface to download, e-mail or publish
 * receipts based on information from specific event registrations.
 */
export default function PrintReceiptsModal({onClose, registrationIds, eventId}) {
  const [receiptIds, setReceiptIds] = useState([]);
  const [downloading, setDownloading] = useState(false);

  const {data: templateList, loading} = useIndicoAxios(allTemplatesURL({event_id: eventId}), {
    trigger: eventId,
    camelize: true,
    skipCamelize: 'placeholders',
  });
  const ready = !loading && !!templateList;

  const makeUpdateTemplateFields = form => templateId => {
    const {customFields, defaultFilename, title} = templateList.find(t => t.id === templateId);
    form.change(
      'custom_fields',
      customFields
        ? Object.assign({}, ...customFields.map(f => ({[f.name]: getDefaultFieldValue(f)})))
        : {}
    );
    form.change('filename', defaultFilename || formatters.slugify(title));
  };

  const downloadReceipts = async format => {
    setDownloading(true);
    try {
      const {data: downloadedData} = await indicoAxios.post(
        exportReceiptsURL(snakifyKeys({eventId, format})),
        snakifyKeys({receiptIds}),
        {responseType: 'blob'}
      );
      downloadBlob(archiveFilename[format], downloadedData);
    } catch (error) {
      handleAxiosError(error);
    }
    setDownloading(false);
  };

  const getCustomFields = templateId =>
    ready && templateList.find(tpl => tpl.id === templateId)?.customFields;

  return (
    <FinalModalForm
      id="print-receipts"
      size="large"
      onSubmit={async values => {
        const {receiptIds: printedReceiptIds, error} = await printReceipt(
          eventId,
          registrationIds,
          values
        );
        if (error) {
          return error;
        } else if (printedReceiptIds.length > 0) {
          setReceiptIds(printedReceiptIds);
        }
      }}
      initialValues={{
        custom_fields: {},
        document_type: 'none',
        filename: 'document',
        save_config: true,
      }}
      onClose={() => onClose(receiptIds.length > 0)}
      header={Translate.string('Generate Documents')}
      keepDirtyOnReinitialize
      noSubmitButton
      disabledAfterSubmit
    >
      {fprops => (
        <>
          <Message color={receiptIds.length === 0 ? 'teal' : 'green'}>
            <Icon name="print" size="big" />
            {receiptIds.length === 0 ? (
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
              <PluralTranslate count={receiptIds.length}>
                <Singular>Successfully generated document for a single registrant</Singular>
                <Plural>
                  Successfully generated{' '}
                  <Param name="numberOfReceipts" value={receiptIds.length} wrapper={<strong />} />{' '}
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
                placeholder={Translate.string('Select a document template')}
                options={
                  ready
                    ? templateList.map(({id, title}) => ({key: id, text: title, value: id}))
                    : []
                }
                onChange={makeUpdateTemplateFields(fprops.form)}
                disabled={receiptIds.length > 0}
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
                    disabled={receiptIds.length > 0}
                    fetchImagesURL={eventImagesURL({event_id: eventId})}
                    defaultOpen
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
                    disabled={!template || receiptIds.length > 0}
                    format={v => formatters.slugify(v).replace(/\.pdf$/, '')}
                    formatOnBlur
                    required
                    fluid
                  />
                )}
              </Field>
              <FinalCheckbox
                name="save_config"
                label={Translate.string('Remember settings')}
                description={Translate.string(
                  'Prefill template parameters (if present) and filename when generating more ' +
                    'documents for the same template in this event.'
                )}
                disabled={receiptIds.length > 0}
              />
              <FinalCheckbox
                name="publish"
                label={Translate.string('Publish document')}
                description={PluralTranslate.string(
                  'Make the resulting document available on the registration page.',
                  'Make the resulting documents available on the registration pages.',
                  registrationIds.length
                )}
                disabled={receiptIds.length > 0}
              />
              <Field name="publish" subscription={{value: true}}>
                {({input: {value: publish}}) => (
                  <FinalCheckbox
                    name="notify_users"
                    label={PluralTranslate.string(
                      'Notify registrants via e-mail',
                      'Notify registrants via e-mail',
                      registrationIds.length
                    )}
                    description={
                      publish
                        ? PluralTranslate.string(
                            'Send an e-mail to the registrant informing them that the document is available.',
                            'Send an e-mail to the registrants informing them that the document is available.',
                            registrationIds.length
                          )
                        : PluralTranslate.string(
                            'Send an e-mail to the registrant with the document attached.',
                            'Send an e-mail to the registrants with the document attached.',
                            registrationIds.length
                          )
                    }
                    disabled={receiptIds.length > 0}
                  />
                )}
              </Field>
              <Form.Group style={{alignItems: 'center'}}>
                <FormSpy subscription={{values: true}}>
                  {({values}) => (
                    <FinalSubmitButton
                      label={makeSubmitLabel(values, registrationIds.length)}
                      icon={values.notify_users ? 'send' : 'save'}
                      style={{width: '100%'}}
                      disabledAfterSubmit
                      fluid
                    />
                  )}
                </FormSpy>
                {receiptIds.length > 0 && (
                  <>
                    <Icon name="check" color="green" size="large" />
                    <Dropdown
                      options={downloadOptions}
                      scrolling
                      icon={null}
                      value={null}
                      selectOnBlur={false}
                      selectOnNavigation={false}
                      onChange={(_, {value}) => downloadReceipts(value)}
                      trigger={
                        <Button
                          icon
                          style={{whiteSpace: 'nowrap', marginLeft: '1em'}}
                          type="button"
                          loading={downloading}
                        >
                          <Icon name="download" /> <Translate>Download</Translate>{' '}
                          <Icon name="caret down" />
                        </Button>
                      }
                    />
                  </>
                )}
              </Form.Group>
            </Grid.Column>
            <Grid.Column>
              <Field name="template" subscription={{value: true}}>
                {({input: {value: templateId}}) => (
                  <Field name="custom_fields" subscription={{value: true}}>
                    {({input: {value: customFields}}) =>
                      templateId ? (
                        <Previewer
                          url={previewReceiptsURL(snakifyKeys({eventId, templateId}))}
                          data={snakifyKeys({customFields, registrationIds})}
                        />
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
                )}
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
