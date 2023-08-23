// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import printReceiptsURL from 'indico-url:receipts.print_receipts';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, ButtonGroup, Icon, Label, Message, Modal} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {injectModal} from 'indico/react/util';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {downloadBlob} from 'indico/utils/browser';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

/**
 * This modal shows to the user any non-fatal templating errors which may have happened during
 * the templating process. The user may choose to download the result anyway (pre-downloaded by
 * the browser).
 */
function PrintingErrorsModal({onClose, errors, downloadData}) {
  const [open, setOpen] = useState(true);
  return (
    <Modal open={open} onClose={onClose} closeIcon>
      <Modal.Header>
        <Translate>Templating Errors</Translate>
      </Modal.Header>
      <Modal.Content>
        <Message error>
          <Translate>There were some templating errors trying to print your documents.</Translate>
        </Message>
        {errors.map(({registration, undefineds}) => (
          <div key={registration.id}>
            <Label>
              {registration.firstName} {registration.lastName}
            </Label>
            {undefineds.map(name => (
              <Label key={`${registration.id}-${name}`} color="red">
                {name}
              </Label>
            ))}
          </div>
        ))}
      </Modal.Content>
      <Modal.Actions>
        <ButtonGroup>
          <Button
            onClick={() => {
              downloadBlob(Translate.string('receipts.pdf'), downloadData);
              setOpen(false);
              onClose();
            }}
            primary
          >
            <Icon name="download" />
            <Translate>Download anyway</Translate>
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
  downloadData: PropTypes.instanceOf(Blob).isRequired,
};

/**
 * Handle the printing logic for a given template on a given event, based on previous user input.
 *
 * @param {number} eventId - Event ID
 * @param {number} templateId - Template ID
 * @param {Array.<String>} registrationIds - IDs of registrants to print
 * @param {String} action - action ("download" | "mail" | "publish")
 * @param {boolean} notifyEmail - whether to notify the user via e-mail (in case "publish" is chosen)
 * @param {Array.<Object>} customFields - custom field values to use in the template
 */
export async function printReceipt(
  eventId,
  templateId,
  registrationIds,
  action,
  notifyEmail,
  customFields
) {
  if (action === 'download') {
    try {
      const data = {
        custom_fields: customFields,
        notify_emaik: notifyEmail,
        registration_ids: registrationIds,
      };
      const {headers, data: downloadedData} = await indicoAxios.post(
        printReceiptsURL(snakifyKeys({eventId, templateId})),
        data,
        {responseType: 'blob'}
      );
      const tplErrors = headers['x-indico-template-errors'];
      if (tplErrors) {
        await new Promise(resolve => {
          injectModal(resolveModal => (
            <PrintingErrorsModal
              onClose={() => {
                resolve();
                resolveModal();
              }}
              errors={camelizeKeys(JSON.parse(tplErrors))}
              downloadData={downloadedData}
            />
          ));
        });
      } else {
        downloadBlob(Translate.string('receipts.pdf'), downloadedData);
        return true;
      }
    } catch (error) {
      handleAxiosError(error);
    }
  } else {
    // XXX: implement 'mail' and 'publish' actions
    window.alert('Not implemented, sorry!');
  }

  return false;
}
