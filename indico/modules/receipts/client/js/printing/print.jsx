// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import printReceiptsURL from 'indico-url:receipts.generate_receipts';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, ButtonGroup, Icon, Label, Message, Modal, Table} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {injectModal} from 'indico/react/util';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

/**
 * This modal shows to the user any non-fatal templating errors which may have happened during
 * the templating process. The user may choose to download the result anyway (pre-downloaded by
 * the browser).
 */
function PrintingErrorsModal({onRetry, onClose, errors}) {
  const [open, setOpen] = useState(true);
  return (
    <Modal open={open} onClose={onClose} closeIcon>
      <Modal.Header>
        <Translate>Templating Errors</Translate>
      </Modal.Header>
      <Modal.Content>
        <Message error>
          <Translate>There were some errors while trying to generate your documents.</Translate>
        </Message>
        <Table celled fixed>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>
                <Translate>Registrant's name</Translate>
              </Table.HeaderCell>
              <Table.HeaderCell>
                <Translate>Missing fields</Translate>
              </Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {errors.map(({registration, undefineds}) => (
              <Table.Row key={registration.id}>
                <Table.Cell>{registration.fullName}</Table.Cell>
                <Table.Cell>
                  {undefineds.map(name => (
                    <Label key={`${registration.id}-${name}`} color="red">
                      {name}
                    </Label>
                  ))}
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </Modal.Content>
      <Modal.Actions>
        <ButtonGroup>
          <Button
            onClick={async () => {
              await onRetry();
              setOpen(false);
              onClose();
            }}
            primary
          >
            <Icon name="sync" />
            <Translate>Generate anyway</Translate>
          </Button>
          <Button
            onClick={() => {
              setOpen(false);
              onClose();
            }}
          >
            <Translate>Cancel</Translate>
          </Button>
        </ButtonGroup>
      </Modal.Actions>
    </Modal>
  );
}

PrintingErrorsModal.propTypes = {
  onRetry: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(
    PropTypes.shape({
      registration: PropTypes.shape({
        firstName: PropTypes.string,
        lastName: PropTypes.string,
      }),
      undefineds: PropTypes.arrayOf(PropTypes.string),
    })
  ).isRequired,
};

/**
 * Handle the printing logic for a given template on a given event, based on previous user input.
 *
 * @param {number} eventId - Event ID
 * @param {Array.<String>} registrationIds - IDs of registrants to print
 * @param {Array.<Object>} values - custom field values to use in the template
 */
export async function printReceipt(eventId, registrationIds, values) {
  const printReceiptsRequest = async (registrations, force) => {
    const {template: templateId, ...data} = values;
    data.registration_ids = registrations;
    data.force = force;
    const resp = await indicoAxios.post(printReceiptsURL(snakifyKeys({eventId, templateId})), data);
    return resp.data;
  };
  try {
    const data = await printReceiptsRequest(registrationIds, false);
    let receiptIds = data.receipt_ids;
    if (data.errors.length) {
      await new Promise(resolve => {
        injectModal(resolveModal => (
          <PrintingErrorsModal
            onRetry={async () => {
              const retryData = await printReceiptsRequest(
                [...new Set(data.errors.map(e => e.registration.id))],
                true
              );
              receiptIds = [...receiptIds, ...retryData.receipt_ids];
            }}
            onClose={() => {
              resolve();
              resolveModal();
            }}
            errors={camelizeKeys(data.errors)}
          />
        ));
      });
    }
    return {receiptIds, error: null};
  } catch (error) {
    return {receiptIds: null, error: handleSubmitError(error)};
  }
}
