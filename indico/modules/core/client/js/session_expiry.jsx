// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

// Enable to get useful debug output in the console. It's recommended to set a session
// lifetime of 1300 in indico.conf when using debug mode.
const DEBUG = false;

const REFRESH_EXPIRY_INTERVAL = 60000;
const REFRESH_EXPIRY_THRESHOLD = DEBUG ? 1500 : 600;
const THRESHOLDS = DEBUG
  ? [
      1200, // initial
      600, // first snooze
      30, // second snooze - afterwards the snooze option will be replaced with dismiss
    ]
  : [
      300, // initial
      120, // first snooze
      15, // second snooze - afterwards the snooze option will be replaced with dismiss
    ];

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
const debug = (...args) => {
  if (DEBUG) {
    console.debug(...args);
  }
};

function SessionExpiryManager({initialExpiry, hardExpiry}) {
  const [expiry, setExpiry] = useState(moment.utc(initialExpiry));
  const [expiryRefreshed, setExpiryRefreshed] = useState(moment.utc());
  const [dialogCountdown, setDialogCountdown] = useState(null);
  const [extending, setExtending] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [snoozeLevel, setSnoozeLevel] = useState(0);

  const updateExpiry = (newExpiry, broadcast = true) => {
    setExpiry(moment.utc(newExpiry));
    if (broadcast) {
      sessionExpiryChannel.postMessage({expiry: newExpiry, fromInit: false});
    }
  };

  const currentDialogThreshold = THRESHOLDS[snoozeLevel];

  useInterval(
    useCallback(async () => {
      const remaining = getTimeLeft(expiry);
      debug(
        'expiry',
        remaining,
        'show threshold',
        currentDialogThreshold,
        'data age',
        (moment.utc() - expiryRefreshed) / 1000,
        'snooze level',
        snoozeLevel,
        'dismissed',
        dismissed
      );

      if (
        remaining < REFRESH_EXPIRY_THRESHOLD &&
        moment.utc() - expiryRefreshed > REFRESH_EXPIRY_INTERVAL && // refresh again if stale
        (dialogCountdown === null || dialogCountdown > 0) // unless the session expired
      ) {
        setExpiryRefreshed(moment.utc());
        const {expiry: newExpiry, error} = await getCurrentSessionExpiry();
        if (!error) {
          debug('new expiry', newExpiry);
          if (newExpiry) {
            updateExpiry(newExpiry, false);
          }
        }
      }
      if (remaining <= currentDialogThreshold) {
        setDialogCountdown(Math.max(0, remaining));
      } else {
        setExtending(false);
        setDialogCountdown(null);
      }
    }, [expiry, expiryRefreshed, currentDialogThreshold, dialogCountdown, snoozeLevel, dismissed]),
    1000
  );

  useEffect(() => {
    const handler = evt => {
      debug('received new expiry', evt.data);
      if (dialogCountdown === 0) {
        // the session is gone, and with it the CSRF token... and syncing a new one between tabs
        // is way too much complexity, so we just require a new login everywhere
        debug('ignoring new expiry on expired session');
        return;
      }
      const {expiry: newExpiry, fromInit} = evt.data;
      updateExpiry(newExpiry, false);
      setExpiryRefreshed(moment.utc());
      if (!fromInit) {
        setSnoozeLevel(0);
      }
      const newRemaining = Math.max(0, getTimeLeft(moment.utc(newExpiry)));
      setDialogCountdown(newRemaining < currentDialogThreshold ? newRemaining : null);
      setDismissed(false);
    };
    sessionExpiryChannel.addEventListener('message', handler);
    return () => sessionExpiryChannel.removeEventListener('message', handler);
  }, [dialogCountdown, currentDialogThreshold]);

  const handleExtend = async () => {
    setExtending(true);
    await indicoAxios.post(sessionRefreshURL());
    const {expiry: newExpiry} = await getCurrentSessionExpiry(false);
    debug('new expiry after refresh', newExpiry, getTimeLeft(moment.utc(newExpiry)));
    updateExpiry(newExpiry);
    setDialogCountdown(null); // do not wait for next interval to close
    setSnoozeLevel(0);
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
    const currentSnoozeIndex = THRESHOLDS.findLastIndex(t => dialogCountdown <= t);
    setSnoozeLevel(currentSnoozeIndex + 1);
    setDialogCountdown(null); // do not wait for next interval to close
  };

  const handleDismiss = () => {
    setDialogCountdown(null); // do not wait for next interval to close
    setDismissed(true);
  };

  if (dialogCountdown === null || dismissed) {
    return null;
  }

  debug('showing modal with countdown', dialogCountdown);
  return (
    <Modal
      size="tiny"
      closeIcon={false}
      closeOnDimmerClick={false}
      closeOnEscape={false}
      dimmer="blurring"
      open
    >
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
  const maxSnoozeReached = remaining <= THRESHOLDS[THRESHOLDS.length - 1];
  const canDismiss = expired || maxSnoozeReached;
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
            <>
              <Translate as="p">
                Your session will expire soon and you need to log in again to renew it if you wish
                to continue using Indico.
              </Translate>
              {canDismiss && (
                <Translate as="p">
                  If you dismiss this message, it will not show up until after your session has
                  expired
                </Translate>
              )}
            </>
          ) : (
            <>
              <Translate as="p">
                Click on the "Refresh" button if you wish to continue using Indico or you will be
                logged out.
              </Translate>
              {canDismiss && (
                <Translate as="p">
                  If you dismiss this message, it will not show up until your session expired.
                </Translate>
              )}
            </>
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
        {canDismiss && (
          <Button onClick={onDismiss}>
            <Translate>Dismiss</Translate>
          </Button>
        )}
        {!canDismiss && hardExpiry && (
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
  sessionExpiryChannel.postMessage({expiry: sessionExpiry, fromInit: true});
  ReactDOM.render(
    <SessionExpiryManager initialExpiry={sessionExpiry} hardExpiry={hardExpiry} />,
    root
  );
});
