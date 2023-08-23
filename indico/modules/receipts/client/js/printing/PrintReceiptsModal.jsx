// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import allTemplatesURL from 'indico-url:receipts.all_templates';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Checkbox, Form, Icon, Loader, Message, Modal} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import {printReceipt} from './print.jsx';

import './PrintReceiptsModal.module.scss';

/**
 * This component represents a custom field which can contain a "text" (str), "choice" or "yes/no" (boolean).
 */
function CustomField({name, value, type, options, onChange}) {
  if (type === 'str') {
    return (
      <Form.Input
        label={name}
        name={name}
        value={value}
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else if (type === 'choice') {
    return (
      <Form.Dropdown
        label={name}
        name={name}
        options={options.map(option => ({value: option, key: option, text: option}))}
        value={value}
        selection
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else {
    return (
      <Form.Checkbox
        label={name}
        name={name}
        onChange={(_, {checked}) => onChange(checked)}
        checked={value}
      />
    );
  }
}

function TemplateParameterEditor({customFields, values, onChange}) {
  return customFields.map(({name, type, options}) => (
    <CustomField
      key={name}
      type={type}
      value={values[name]}
      onChange={value => {
        onChange({...values, [name]: value});
      }}
      name={name}
      options={options}
    />
  ));
}

/**
 * This modal presents the user with a structured interface to download, e-mail or publish
 * receipts based on information from specific event registrations.
 */
export default function PrintReceiptsModal({onClose, registrationIds, eventId}) {
  const [selectedTemplateId, setSelectedTemplateId] = useState(null);
  const [selectedAction, setSelectedAction] = useState('download');
  const [open, setOpen] = useState(true);
  const [printing, setPrinting] = useState(false);
  const [notifyEmail, setNotifyEmail] = useState(false);
  const [customFieldValues, setCustomFieldValues] = useState({});

  const {data, loading} = useIndicoAxios({
    url: allTemplatesURL({event_id: eventId}),
    trigger: eventId,
    camelize: true,
  });

  const ready = !loading && !!data;
  const selectedTemplate = ready && data.find(tpl => tpl.id === selectedTemplateId);

  return (
    <Modal open={open} onClose={onClose} closeIcon styleName="modal">
      <Modal.Header>
        <Translate>Print Receipts/Certificates</Translate>
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
        <Form>
          <section>
            <h2>
              <Translate>Document Template</Translate>
            </h2>
            <Form.Dropdown
              loading={!ready}
              value={selectedTemplateId}
              options={ready ? data.map(({id, title}) => ({key: id, text: title, value: id})) : []}
              onChange={(_, {value}) => {
                const {customFields} = data.find(t => t.id === value);
                setCustomFieldValues(
                  Object.assign({}, ...customFields.map(f => ({[f.name]: f.default || null})))
                );
                setSelectedTemplateId(value);
              }}
              selection
            />
          </section>
          {!!selectedTemplate && (
            <section styleName="custom-fields">
              <h3>
                <Translate>Template Parameters</Translate>
              </h3>
              {selectedTemplate ? (
                <TemplateParameterEditor
                  customFields={selectedTemplate.customFields}
                  values={customFieldValues}
                  onChange={vals => {
                    setCustomFieldValues(vals);
                  }}
                />
              ) : (
                <Loader active />
              )}
            </section>
          )}
          <section>
            <h2>
              <Translate>Action</Translate>
            </h2>
            <Button.Group>
              {[
                {icon: 'download', action: 'download', text: Translate.string('Download')},
                {icon: 'eye', action: 'publish', text: Translate.string('Publish')},
                {icon: 'mail', action: 'mail', text: Translate.string('E-mail')},
              ].map(({icon, action, text}) => (
                <Button
                  key={action}
                  disabled={!selectedTemplate}
                  primary={selectedAction === action}
                  onClick={() => setSelectedAction(action)}
                >
                  <Icon name={icon} />
                  {text}
                </Button>
              ))}
            </Button.Group>
            <Message info>
              {selectedAction === 'download' && (
                <Translate>The document(s) will be downloaded immediately</Translate>
              )}
              {selectedAction === 'publish' && (
                <Translate>
                  The resulting receipt(s) will be available from the registration page. You can
                  optionally notify the user about it.
                </Translate>
              )}
              {selectedAction === 'mail' && (
                <Translate>
                  The document(s) will be e-mailed to the corresponding registrants
                </Translate>
              )}
            </Message>
            <div>
              {selectedAction === 'publish' && (
                <Checkbox
                  name="notify_email"
                  label={Translate.string('Notify user via e-mail')}
                  checked={notifyEmail}
                  onChange={(_, {checked}) => setNotifyEmail(checked)}
                />
              )}
            </div>
          </section>
        </Form>
      </Modal.Content>
      <Modal.Actions>
        <Button.Group>
          <Button
            disabled={!selectedTemplate || printing}
            loading={printing}
            primary
            onClick={async () => {
              setPrinting(true);
              const result = await printReceipt(
                eventId,
                selectedTemplateId,
                registrationIds,
                selectedAction,
                notifyEmail,
                customFieldValues
              );
              setPrinting(false);
              if (result) {
                setOpen(false);
                onClose();
              }
            }}
          >
            <Icon name="print" />
            <Translate>Print Receipts</Translate>
          </Button>
          <Button
            onClick={() => {
              setOpen(false);
              onClose();
            }}
          >
            <Translate>Cancel</Translate>
          </Button>
        </Button.Group>
      </Modal.Actions>
    </Modal>
  );
}

PrintReceiptsModal.propTypes = {
  onClose: PropTypes.func.isRequired,
  registrationIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  eventId: PropTypes.number.isRequired,
};
