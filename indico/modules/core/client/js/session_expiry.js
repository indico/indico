// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import loginURL from 'indico-url:auth.login';
import sessionExpiryURL from 'indico-url:core.session_expiry';
import sessionRefreshURL from 'indico-url:core.session_refresh';

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState, useEffect, useReducer, useRef, useCallback} from 'react';
import ReactDOM from 'react-dom';
import {Modal, Button} from 'semantic-ui-react';

import {useInterval} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

const sessionExpiryChannel = new BroadcastChannel('indico-session-expiry');

function sessionExpiryReducer(state, action) {
  switch (action.type) {
    case 'ACTIVATE_SESSION_TIMEOUT':
      return {...state, operation: 'active', count: 120};
    case 'UPDATE_SESSION_EXPIRY':
      return {...state, sessionExpiry: action.sessionExpiry};
    case 'ACTIVATE_SESSION_COUNTDOWN':
      return {...state, operation: 'countdown'};
    case 'UPDATE_SESSION_COUNTDOWN':
      return {...state, count: action.count};
    case 'SESSION_EXPIRE':
      return {...state, operation: 'expired', count: 0};
    case 'RESET':
      return {...state, operation: 'reset'};
    default:
      return state;
  }
}

const sessionExpiryActionsShape = PropTypes.shape({
  onAccept: PropTypes.func.isRequired,
  onReject: PropTypes.func.isRequired,
});

function SessionExpiryCountdown({callback}) {
  useInterval(callback, 1000);
  return null;
}

function SessionExpiryCountdownBody({count, sessionExpiryActions, inProgress}) {
  return (
    <>
      <Modal.Header>
        <Translate>Your current session is about to expire.</Translate>
      </Modal.Header>
      <Modal.Content>
        <>
          <Translate>
            Click on the refresh button if you wish to continue using Indico or you will be logged
            out.
          </Translate>
          <center className="ui large header">{count}</center>
        </>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={sessionExpiryActions.onAccept} disabled={inProgress} loading={inProgress}>
          <Translate>Refresh</Translate>
        </Button>
        <Button onClick={sessionExpiryActions.onReject} disabled={inProgress}>
          <Translate>Cancel</Translate>
        </Button>
      </Modal.Actions>
    </>
  );
}

SessionExpiryCountdown.propTypes = {
  callback: PropTypes.func.isRequired,
};

SessionExpiryCountdownBody.propTypes = {
  count: PropTypes.number.isRequired,
  sessionExpiryActions: sessionExpiryActionsShape.isRequired,
  inProgress: PropTypes.bool.isRequired,
};

function SessionExpiredBody({sessionExpiryActions, inProgress}) {
  return (
    <>
      <Modal.Header>
        <Translate>This session has expired.</Translate>
      </Modal.Header>
      <Modal.Content>
        <Translate>Your current session has expired and you have been logged out.</Translate>
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={sessionExpiryActions.onAccept} disabled={inProgress} loading={inProgress}>
          <Translate>Login again</Translate>
        </Button>
        <Button onClick={sessionExpiryActions.onReject} disabled={inProgress}>
          <Translate>Cancel</Translate>
        </Button>
      </Modal.Actions>
    </>
  );
}

SessionExpiredBody.propTypes = {
  sessionExpiryActions: sessionExpiryActionsShape.isRequired,
  inProgress: PropTypes.bool.isRequired,
};

export default function SessionExpiryManager({initialExpiry, hardExpiry}) {
  const [inProgress, setInProgress] = useState(false);
  const [state, dispatch] = useReducer(sessionExpiryReducer, {
    operation: 'active',
    count: 120,
    sessionExpiry: initialExpiry,
  });
  const sessionTimeout = useRef();
  const opened = useRef(false);
  const {operation, count, sessionExpiry} = state;

  useEffect(() => {
    const handler = evt => {
      dispatch({type: 'UPDATE_SESSION_EXPIRY', sessionExpiry: evt.data});
    };
    sessionExpiryChannel.addEventListener('message', handler);
    return () => sessionExpiryChannel.removeEventListener('message', handler);
  }, []);

  const updateSessionExpiry = useCallback(
    expiry => {
      dispatch({type: 'UPDATE_SESSION_EXPIRY', sessionExpiry: expiry});
      sessionExpiryChannel.postMessage(expiry);
    },
    [dispatch]
  );

  const getFreshSessionExpiry = async url => {
    let response;
    try {
      response = await indicoAxios.get(url);
    } catch (e) {
      return handleAxiosError(e);
    }
    return response.data.session_expiry;
  };

  const sessionExpiryCountdownCallback = () => {
    if (sessionExpiry === null) {
      dispatch({type: 'SESSION_EXPIRE'});
      return;
    }
    const millisecondsLeft = moment.utc(sessionExpiry) - moment.utc();
    const counter = Math.ceil(millisecondsLeft / 1000);
    if (counter >= 0 && counter <= 120) {
      if (!opened.current) {
        opened.current = true;
      }
      dispatch({type: 'UPDATE_SESSION_COUNTDOWN', count: counter});
    } else if (counter < 0) {
      dispatch({type: 'SESSION_EXPIRE'});
    } else if (counter >= 120 && opened.current) {
      opened.current = false;
      dispatch({type: 'ACTIVATE_SESSION_TIMEOUT'});
    }
  };

  const checkTimeToExpire = useCallback(async () => {
    const freshSessionExpiry = await getFreshSessionExpiry(sessionExpiryURL());
    updateSessionExpiry(freshSessionExpiry);
    if (moment.utc().add(120, 'seconds') >= moment.utc(freshSessionExpiry)) {
      dispatch({type: 'ACTIVATE_SESSION_COUNTDOWN'});
    } else {
      dispatch({type: 'ACTIVATE_SESSION_TIMEOUT'});
    }
  }, [updateSessionExpiry]);

  useEffect(() => {
    if (operation === 'active') {
      const delay = Math.max(
        moment.utc(sessionExpiry).subtract('120', 'seconds') - moment.utc(),
        1000
      );
      sessionTimeout.current = setTimeout(checkTimeToExpire, delay);
      return () => clearInterval(sessionTimeout.current);
    }
    if (operation === 'expired') {
      updateSessionExpiry(null);
    }
  }, [sessionExpiry, operation, checkTimeToExpire, updateSessionExpiry]);

  const refreshSession = async () => {
    setInProgress(true);
    const freshSessionExpiry = await getFreshSessionExpiry(sessionRefreshURL());
    updateSessionExpiry(freshSessionExpiry);
    setInProgress(false);
    opened.current = false;
    dispatch({type: 'ACTIVATE_SESSION_TIMEOUT'});
    return true;
  };

  const loginAgain = () => {
    setInProgress(true);
    const hash = location.hash;
    location.href = loginURL({next: location.href + hash});
    setInProgress(false);
    return true;
  };

  const sessionExpiryActions = {
    onAccept: operation === 'expired' || hardExpiry ? loginAgain : refreshSession,
    onReject: () => dispatch({type: 'RESET'}),
  };

  return (
    <>
      {(operation === 'countdown' || operation === 'reset') && (
        <SessionExpiryCountdown callback={sessionExpiryCountdownCallback} />
      )}
      <Modal
        size="tiny"
        closeIcon={false}
        closeOnDimmerClick={!inProgress}
        closeOnEscape={!inProgress}
        open={operation === 'countdown' || operation === 'expired'}
      >
        {operation === 'countdown' && (
          <SessionExpiryCountdownBody
            count={count}
            sessionExpiryActions={sessionExpiryActions}
            inProgress={inProgress}
          />
        )}
        {operation === 'expired' && (
          <SessionExpiredBody sessionExpiryActions={sessionExpiryActions} inProgress={inProgress} />
        )}
      </Modal>
    </>
  );
}

SessionExpiryManager.propTypes = {
  initialExpiry: PropTypes.string.isRequired,
  hardExpiry: PropTypes.bool.isRequired,
};

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#session-expiry-root');
  if (root) {
    const sessionExpiry = root.dataset.sessionExpiry;
    const hardExpiry = root.dataset.hardExpiry !== undefined;
    ReactDOM.render(
      <SessionExpiryManager initialExpiry={sessionExpiry} hardExpiry={hardExpiry} />,
      root
    );
  }
});
