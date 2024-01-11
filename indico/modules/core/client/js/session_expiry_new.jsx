// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import loginURL from 'indico-url:auth.login';
import sessionExpiryURL from 'indico-url:core.session_expiry';
import sessionRefreshURL from 'indico-url:core.session_refresh';

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState, useEffect, useCallback} from 'react';
import ReactDOM from 'react-dom';
import {Modal, Button} from 'semantic-ui-react';

import {useInterval} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

const sessionExpiryChannel = new BroadcastChannel('indico-session-expiry');

const REFRESH_EXPIRY_THRESHOLD = 1500; // TODO lower this
const SHOW_DIALOG_THRESHOLD = 1295; // TODO lower this
const REFRESH_EXPIRY_INTERVAL = 60000;

const getTimeLeft = expiry => Math.max(0, Math.floor((expiry - moment.utc()) / 1000));
const getCurrentSessionExpiry = async (silent = true) => {
  let response;
  try {
    response = await indicoAxios.get(sessionExpiryURL());
  } catch (e) {
    if (!silent) {
      handleAxiosError(e);
    }
    return {error: true, expiry: null};
  }
  return {error: false, expiry: response.data.session_expiry};
};

function SessionExpiryManager({initialExpiry, hardExpiry}) {
  const [expiry, setExpiry] = useState(moment.utc(initialExpiry));
  const [expiryRefreshed, setExpiryRefreshed] = useState(moment.utc());
  const [dialogCountdown, setDialogCountdown] = useState(null);
  const [extending, setExtending] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [snoozeThreshold, setSnoozeThreshold] = useState(null);

  const updateExpiry = (newExpiry, broadcast = true) => {
    setExpiry(moment.utc(newExpiry));
    if (broadcast) {
      sessionExpiryChannel.postMessage(newExpiry);
    }
  };

  const currentDialogThreshold = snoozeThreshold || SHOW_DIALOG_THRESHOLD;

  useInterval(
    useCallback(async () => {
      const remaining = getTimeLeft(expiry);
      // TODO remove console log
      console.log(
        'expiry',
        remaining,
        'show threshold',
        currentDialogThreshold,
        'data age',
        (moment.utc() - expiryRefreshed) / 1000
      );
      if (
        remaining < REFRESH_EXPIRY_THRESHOLD &&
        moment.utc() - expiryRefreshed > REFRESH_EXPIRY_INTERVAL // refresh again if stale
      ) {
        setExpiryRefreshed(moment.utc());
        const {expiry: newExpiry, error} = await getCurrentSessionExpiry();
        if (!error) {
          // TODO remove console log
          console.log('new expiry', newExpiry);
          if (newExpiry) {
            updateExpiry(newExpiry);
          }
        }
      }
      if (remaining < currentDialogThreshold) {
        setDialogCountdown(Math.max(0, remaining));
      } else {
        setExtending(false);
        setDialogCountdown(null);
      }
    }, [expiry, expiryRefreshed, currentDialogThreshold]),
    1000
  );

  useEffect(() => {
    const handler = evt => {
      // TODO remove console log
      console.log('received new expiry', evt.data, dialogCountdown);
      if (dialogCountdown === 0) {
        // the session is gone, and with it the CSRF token... and syncing a new one between tabs
        // is way too much complexity, so we just require a new login everywhere
        // TODO remove console log
        console.log('ignoring new expiry on expired session');
        return;
      }
      updateExpiry(evt.data, false);
      setExpiryRefreshed(moment.utc());
      setDismissed(false);
    };
    sessionExpiryChannel.addEventListener('message', handler);
    return () => sessionExpiryChannel.removeEventListener('message', handler);
  }, [dialogCountdown]);

  const handleExtend = async () => {
    setExtending(true);
    await indicoAxios.post(sessionRefreshURL());
    const {expiry: newExpiry} = await getCurrentSessionExpiry(false);
    // TODO remove console log
    console.log('new expiry after refresh', newExpiry, getTimeLeft(moment.utc(newExpiry)));
    updateExpiry(newExpiry);
    setDialogCountdown(null); // do not wait for next interval to close
    setSnoozeThreshold(null);
    setExtending(false);
  };

  const handleLogin = () => {
    const url = loginURL({next: location.href + location.hash, force: 1});
    location.href = url;
  };

  const handleSnooze = () => {
    // we do not broadcast snooze to other tabs on purpose since people may just want to finish
    // something in one tab, but not necessarily in another one (where they may end up refreshing
    // or logging in again)
    setSnoozeThreshold(Math.ceil(dialogCountdown / 2));
    setDialogCountdown(null); // do not wait for next interval to close
  };

  const handleDismiss = () => {
    setDialogCountdown(null); // do not wait for next interval to close
    setDismissed(true);
  };

  if (dialogCountdown === null || dismissed) {
    return null;
  }

  // TODO remove console log
  console.log('rendered time', dialogCountdown);
  return (
    <Modal size="tiny" closeIcon={false} closeOnDimmerClick={false} closeOnEscape={false} open>
      <SessionExpiryCountdownBody
        remaining={dialogCountdown}
        onRefresh={handleExtend}
        onLogin={handleLogin}
        onSnooze={handleSnooze}
        onDismiss={handleDismiss}
        inProgress={extending}
        hardExpiry={hardExpiry}
      />
    </Modal>
  );
}

SessionExpiryManager.propTypes = {
  initialExpiry: PropTypes.string.isRequired,
  hardExpiry: PropTypes.bool.isRequired,
};

function SessionExpiryCountdownBody({
  remaining,
  onRefresh,
  onLogin,
  onSnooze,
  onDismiss,
  inProgress,
  hardExpiry,
}) {
  const expired = remaining === 0;
  return (
    <>
      <Modal.Header>
        {expired ? (
          <Translate>Your session expired</Translate>
        ) : (
          <Translate>Your current session is about to expire</Translate>
        )}
      </Modal.Header>
      <Modal.Content>
        <>
          {expired ? (
            <>
              <p>
                <Translate>
                  Your session has expired and you have been logged out. Please log in again if you
                  wish to continue using Indico.
                </Translate>
              </p>
              <p>
                <Translate>
                  If you need to save anything, you can also dismiss this message, but any
                  operations on the current page will fail until you manually log in again.
                </Translate>
              </p>
            </>
          ) : hardExpiry ? (
            <Translate>
              Your session will expire soon and you need to log in again to renew it if you wish to
              continue using Indico.
            </Translate>
          ) : (
            <Translate>
              Click on the "Refresh" button if you wish to continue using Indico or you will be
              logged out.
            </Translate>
          )}
          {!expired && <center className="ui large header">{remaining}</center>}
        </>
      </Modal.Content>
      <Modal.Actions>
        {hardExpiry || expired ? (
          <Button primary onClick={onLogin} disabled={inProgress} loading={inProgress}>
            <Translate>Login again</Translate>
          </Button>
        ) : (
          <Button primary onClick={onRefresh} disabled={inProgress} loading={inProgress}>
            <Translate>Refresh</Translate>
          </Button>
        )}
        {expired ? (
          <Button onClick={onDismiss}>
            <Translate>Dismiss</Translate>
          </Button>
        ) : (
          <Button onClick={onSnooze} disabled={inProgress}>
            <Translate>Snooze</Translate>
          </Button>
        )}
      </Modal.Actions>
    </>
  );
}

SessionExpiryCountdownBody.propTypes = {
  remaining: PropTypes.number.isRequired,
  onRefresh: PropTypes.func.isRequired,
  onLogin: PropTypes.func.isRequired,
  onSnooze: PropTypes.func.isRequired,
  onDismiss: PropTypes.func.isRequired,
  inProgress: PropTypes.bool.isRequired,
  hardExpiry: PropTypes.bool.isRequired,
};

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#session-expiry-root');
  if (!root) {
    return;
  }
  const sessionExpiry = root.dataset.sessionExpiry;
  const hardExpiry = root.dataset.hardExpiry !== undefined;
  sessionExpiryChannel.postMessage(sessionExpiry);
  ReactDOM.render(
    <SessionExpiryManager initialExpiry={sessionExpiry} hardExpiry={hardExpiry} />,
    root
  );
});
