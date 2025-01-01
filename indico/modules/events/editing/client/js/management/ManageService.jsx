// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import checkServiceURL from 'indico-url:event_editing.api_check_service_url';
import connectServiceURL from 'indico-url:event_editing.api_service_connect';
import disconnectServiceURL from 'indico-url:event_editing.api_service_disconnect';
import checkServiceStatusURL from 'indico-url:event_editing.api_service_status';

import {FORM_ERROR} from 'final-form';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Confirm, Modal, Button, Form, Loader, Message} from 'semantic-ui-react';

import {
  FinalSubmitButton,
  FinalInput,
  handleSubmitError,
  validators as v,
} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate, Param} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import Section from './Section';

const debounce = makeAsyncDebounce(250);

export default function ManageService({eventId}) {
  const [serviceURLInfo, setServiceURLInfo] = useState(false);
  const [connectOpen, setConnectOpen] = useState(false);
  const [disconnectOpen, setDisconnectOpen] = useState(false);
  const {data, error, loading, reFetch} = useIndicoAxios(
    checkServiceStatusURL({event_id: eventId}),
    {camelize: true}
  );

  const checkPending = loading || (data === null && error === null);
  let label = Translate.string('Custom editing workflow');
  let description;
  let showConnect = false;
  let showDisconnect = false;
  let forceDisconnect = false;

  if (checkPending) {
    description = Translate.string('Checking custom editing workflow status');
  } else if (error || data.error) {
    description = Translate.string('Workflow service unavailable: {error}', {
      error: error || data.error,
    });
    // allow disconnecting if the service returned an error, not if our own request failed
    if (error === null) {
      showDisconnect = true;
      forceDisconnect = true;
    }
  } else if (!data.connected) {
    description = Translate.string('Use a custom editing workflow provided by an external service');
    showConnect = true;
  } else {
    label = (
      <Translate>
        Custom editing workflow: <Param name="name" value={data.status.service.name} /> (
        <Param name="version" value={data.status.service.version} />)
      </Translate>
    );
    description = Translate.string('Connected to a custom editing workflow service');
    showDisconnect = data.status.canDisconnect;
  }

  if (showDisconnect) {
    description = (
      <>
        {description} (
        <a onClick={() => setDisconnectOpen(true)}>
          <Translate>disconnect</Translate>
        </a>
        )
      </>
    );
  }

  const closeConnectModal = () => {
    setServiceURLInfo(null);
    setConnectOpen(false);
  };

  const connect = async ({url}) => {
    try {
      await indicoAxios.post(connectServiceURL({event_id: eventId}), {url});
    } catch (err) {
      return handleSubmitError(err);
    }
    closeConnectModal();
    reFetch();
  };

  const disconnect = async () => {
    try {
      await indicoAxios.post(disconnectServiceURL({event_id: eventId}), {force: forceDisconnect});
    } catch (err) {
      handleAxiosError(err);
      return;
    }
    setDisconnectOpen(false);
    reFetch();
  };

  return (
    <Section icon="puzzle" label={label} description={description}>
      {showConnect && (
        <button type="button" className="i-button icon-puzzle" onClick={() => setConnectOpen(true)}>
          <Translate>Connect</Translate>
        </button>
      )}
      {loading && <Loader active inline />}
      <Confirm
        size="tiny"
        open={disconnectOpen}
        onCancel={() => setDisconnectOpen(false)}
        onConfirm={disconnect}
        confirmButton={<Button content={Translate.string('Disconnect')} negative />}
        header={Translate.string('Disconnect editing workflow service')}
        content={
          <Modal.Content>
            {forceDisconnect ? (
              <Translate>
                Disconnecting the editing workflow service while it is unavailable may leave your
                editing process in an inconsistent state. Do not perform this action if you plan to
                continue using the workflow service later.{' '}
                <Param name="strong" wrapper={<strong />}>
                  The current error with the workflow service is most likely temporary. Attempting
                  to disconnect and reconnect will most likely not fix it.
                </Param>
              </Translate>
            ) : (
              <Translate>
                Do you really want to disconnect from the editing workflow service? If your editing
                process has already started (e.g. people submitted content to be edited),
                disconnecting is most likely not a good idea and should only be done if you do not
                plan to enable the service again for this event.
              </Translate>
            )}
          </Modal.Content>
        }
      />
      <Modal size="small" open={connectOpen} onClose={closeConnectModal}>
        <FinalForm onSubmit={connect} subscription={{}}>
          {fprops => (
            <>
              <Modal.Header content={Translate.string('Connect to editing workflow service')} />
              <Modal.Content>
                <Message warning>
                  {/* This message is not translated because it will be removed soon-ish. */}
                  This feature is still <strong>experimental</strong>. Especially if you are not the
                  administrator of this Indico instance be aware that even minor Indico upgrades may
                  contain backwards-incompatible changes to the API between Indico and the service.
                </Message>
                <Form id="connect-service-form" onSubmit={fprops.handleSubmit}>
                  <FinalInput
                    name="url"
                    label={Translate.string('Service URL')}
                    description={
                      <Translate>
                        Provide the URL for the service implementing your custom editing workflow.
                      </Translate>
                    }
                    autoFocus
                    required
                    validate={async value => {
                      setServiceURLInfo(null);

                      const validationError = v.required(value) || v.url(value);
                      if (validationError) {
                        return validationError;
                      }

                      let resp;
                      try {
                        // this does send a request on each keypress, but in this particular case
                        // it's VERY likely that people paste a url, so it shouldn't be an issue
                        resp = await debounce(() =>
                          indicoAxios.get(checkServiceURL({event_id: eventId}), {
                            params: {url: value},
                          })
                        );
                      } catch (err) {
                        // the url validation is not exactly the same on the client and server
                        // side, so we have some edge cases (e.g. `http://test:`) which pass
                        // the client-side check but not the server-side one.
                        // in this case we do not want an error dialog to show up but rather
                        // fail validation nicely.
                        const submitError = handleSubmitError(err);
                        return submitError.url || submitError[FORM_ERROR];
                      }

                      if (resp.data.error) {
                        return resp.data.error;
                      }

                      setServiceURLInfo(resp.data.info);
                    }}
                  />
                  {serviceURLInfo ? (
                    <Message info>
                      <Translate>
                        Your editing workflow will be managed by{' '}
                        <Param name="service" value={serviceURLInfo.name} wrapper={<strong />} /> (
                        <Param name="version" value={serviceURLInfo.version} />
                        ).
                      </Translate>
                      <br />
                      <Translate>
                        Please note that connecting to this service may immediately update your
                        editing settings and create e.g. new tags and file types. Only connect if
                        you intend to use this workflow in your event!
                      </Translate>
                    </Message>
                  ) : (
                    <Message info>
                      <Translate>
                        If you are a developer looking to implement a custom workflow, head over to
                        the{' '}
                        <Param
                          name="link"
                          wrapper={
                            <a
                              href="https://github.com/indico/openreferee/"
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{fontWeight: 'bold'}}
                            />
                          }
                        >
                          reference implementation of the OpenReferee spec on GitHub
                        </Param>
                        .
                      </Translate>
                    </Message>
                  )}
                </Form>
              </Modal.Content>
              <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
                <FinalSubmitButton
                  form="connect-service-form"
                  label={Translate.string('Connect')}
                />
                <Button onClick={closeConnectModal}>
                  <Translate>Cancel</Translate>
                </Button>
              </Modal.Actions>
            </>
          )}
        </FinalForm>
      </Modal>
    </Section>
  );
}

ManageService.propTypes = {
  eventId: PropTypes.number.isRequired,
};
