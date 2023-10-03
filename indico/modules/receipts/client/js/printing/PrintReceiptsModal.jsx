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
import {
  Accordion,
  Button,
  Checkbox,
  Form,
  Grid,
  Icon,
  Input,
  Loader,
  Message,
  Modal,
} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import Previewer from '../templates/Previewer.jsx';

import {printReceipt} from './print.jsx';
import TemplateParameterEditor from './TemplateParameterEditor.jsx';

import './PrintReceiptsModal.module.scss';

/**
 * This modal presents the user with a structured interface to download, e-mail or publish
 * receipts based on information from specific event registrations.
 */
export default function PrintReceiptsModal({onClose, registrationIds, eventId}) {
  const [selectedTemplateId, setSelectedTemplateId] = useState(null);
  const [open, setOpen] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [receipts, setReceipts] = useState([]);
  const [notifyEmail, setNotifyEmail] = useState(false);
  const [customFieldValues, setCustomFieldValues] = useState({});

  const {data, loading} = useIndicoAxios(allTemplatesURL({event_id: eventId}), {
    trigger: eventId,
    camelize: true,
  });
  const ready = !loading && !!data;
  const selectedTemplate = ready && data.find(tpl => tpl.id === selectedTemplateId);

  return (
    <Modal open={open} onClose={onClose} closeIcon styleName="modal" size="large">
      <Modal.Header>
        <Translate>Generate Documents</Translate>
      </Modal.Header>
      <Modal.Content>
        <Message color="teal">
          <Icon name="print" size="big" />
          <PluralTranslate count={registrationIds.length}>
            <Singular>Generating document for a single registrant</Singular>
            <Plural>
              Printing documents for{' '}
              <Param
                name="numberOfRegistrants"
                value={registrationIds.length}
                wrapper={<strong />}
              />{' '}
              registrants
            </Plural>
          </PluralTranslate>
        </Message>
        <Grid columns={selectedTemplate ? 2 : 1} divided>
          <Grid.Column>
            <Form>
              <section>
                <h2>
                  <Translate>Document Template</Translate>
                </h2>
                <Form.Dropdown
                  loading={!ready}
                  value={selectedTemplateId}
                  placeholder={Translate.string('Select a receipt template')}
                  options={
                    ready ? data.map(({id, title}) => ({key: id, text: title, value: id})) : []
                  }
                  onChange={(_, {value}) => {
                    const {customFields} = data.find(t => t.id === value);
                    setCustomFieldValues(
                      customFields
                        ? Object.assign({}, ...customFields.map(f => ({[f.name]: f.default || null})))
                        : {}
                    );
                    setSelectedTemplateId(value);
                  }}
                  selection
                />
                {!!selectedTemplate && selectedTemplate.customFields.length > 0 && (
                  <Accordion
                    defaultActiveIndex={0}
                    panels={[
                      {
                        key: 'template-params',
                        title: Translate.string('Template Parameters'),
                        content: {
                          content: selectedTemplate ? (
                            <TemplateParameterEditor
                              customFields={selectedTemplate.customFields}
                              values={customFieldValues}
                              onChange={vals => {
                                setCustomFieldValues(vals);
                              }}
                            />
                          ) : (
                            <Loader active />
                          ),
                        },
                      },
                    ]}
                    styled
                    fluid
                  />
                )}
              </section>
              <section>
                <h2>
                  <Translate>Generate</Translate>
                </h2>
                <Form.Group>
                  <Input label={Translate.string('Document type')} />
                  <Input label={Translate.string('File name')} />
                </Form.Group>
                <Checkbox
                  name="publish"
                  label={Translate.string('Publish document')}
                  checked={notifyEmail}
                  onChange={(_, {checked}) => setNotifyEmail(checked)}
                />
                <Message info>
                  <Translate>
                    The resulting receipt(s) will be available from the registration page. You can
                    optionally notify the user about it.
                  </Translate>
                </Message>
                <Checkbox
                  name="notify_email"
                  label={Translate.string('Notify user via e-mail')}
                  checked={notifyEmail}
                  onChange={(_, {checked}) => setNotifyEmail(checked)}
                />
                <Button
                  disabled={!selectedTemplate || generating}
                  loading={generating}
                  primary={receipts.length === 0}
                  onClick={async () => {
                    setGenerating(true);
                    const result = await printReceipt(
                      eventId,
                      selectedTemplateId,
                      registrationIds,
                      customFieldValues
                    );
                    setGenerating(false);
                    if (result) {
                      console.log(result);
                      setReceipts(result.receipts);
                    }
                  }}
                >
                  <Icon name="sync" />
                  <Translate>Generate</Translate>
                </Button>
                {receipts.length > 0 && <Icon name="check" color="green" />}
              </section>
              <section>
                <h2>
                  <Translate>Action</Translate>
                </h2>
                <Button.Group>
                  {[
                    {icon: 'download', action: 'download', text: Translate.string('Download')},
                    {icon: 'mail', action: 'mail', text: Translate.string('E-mail')},
                  ].map(({icon, action, text}) => (
                    <Button key={action} disabled={!selectedTemplate}>
                      <Icon name={icon} />
                      {text}
                    </Button>
                  ))}
                </Button.Group>
                <Message info>
                  {'' === 'download' && (
                    <Translate>The document(s) will be downloaded immediately</Translate>
                  )}
                  {'' === 'mail' && (
                    <Translate>
                      The document(s) will be e-mailed to the corresponding registrants
                    </Translate>
                  )}
                </Message>
              </section>
            </Form>
          </Grid.Column>
          {selectedTemplate && (
            <Grid.Column>
              <Previewer
                url={previewReceiptsURL({event_id: eventId, template_id: selectedTemplateId})}
                data={{custom_fields: customFieldValues, registration_ids: registrationIds}}
              />
            </Grid.Column>
          )}
        </Grid>
      </Modal.Content>
      <Modal.Actions>
        <Button
          onClick={() => {
            setOpen(false);
            onClose();
          }}
          primary={receipts.length > 0}
          content={receipts.length > 0 ? Translate.string('Close') : Translate.string('Cancel')}
        />
      </Modal.Actions>
    </Modal>
  );
}

PrintReceiptsModal.propTypes = {
  onClose: PropTypes.func.isRequired,
  registrationIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  eventId: PropTypes.number.isRequired,
};
