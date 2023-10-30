// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import loginURL from 'indico-url:auth.login';
import sessionExpirationURL from 'indico-url:core.session_expiration';
import sessionRefreshURL from 'indico-url:core.session_refresh';

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState, useEffect, useReducer, useRef, useCallback} from 'react';
import ReactDOM from 'react-dom';
import {Modal, Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

function sessionExpirationReducer(state, action) {
  switch (action.type) {
    case 'ACTIVATE_SESSION_TIMER':
      return {operation: 'active', count: 120};
    case 'START_SESSION_COUNTDOWN':
      return {operation: 'countdown', count: action.count};
    case 'UPDATE_SESSION_COUNTDOWN':
      return {...state, count: action.count};
    case 'SESSION_EXPIRE':
      return {operation: 'expired', count: 0};
    case 'RESET':
      return {operation: 'reset'};
    default:
      return state;
  }
}

export default function SessionExpirationManager({hardExpiry}) {
  const [inProgress, setInProgress] = useState(false);
  const [state, dispatch] = useReducer(sessionExpirationReducer, {operation: 'active'});
  const trackSessionInterval = useRef();
  const countdownInterval = useRef();
  const opened = useRef(false);
  const {operation, count} = state;

  const sessionExpirationCountdownActions = useCallback(() => {
    const expiration = localStorage.getItem('session-expiration');
    if (expiration === null) {
      clearInterval(countdownInterval.current);
      dispatch({type: 'SESSION_EXPIRE'});
      return;
    }
    const sessionExpiration = moment.utc(expiration);
    const millisecondsLeft = sessionExpiration - moment.utc();
    const counter = Math.ceil(millisecondsLeft / 1000);
    if (counter >= 0 && counter <= 120) {
      if (!opened.current) {
        dispatch({type: 'START_SESSION_COUNTDOWN', count: counter});
        opened.current = true;
      }
      dispatch({type: 'UPDATE_SESSION_COUNTDOWN', count: counter});
    } else if (counter < 0) {
      clearInterval(countdownInterval.current);
      dispatch({type: 'SESSION_EXPIRE'});
    } else if (counter >= 120 && opened.current) {
      opened.current = false;
      clearInterval(countdownInterval.current);
      dispatch({type: 'ACTIVATE_SESSION_TIMER'});
    }
  }, []);

  const getSessionExpirationTime = async () => {
    let response;
    try {
      response = await indicoAxios.get(sessionExpirationURL());
    } catch (e) {
      return handleAxiosError(e);
    }
    return response.data.session_expiration;
  };

  const checkTimeToExpire = useCallback(async () => {
    let sessionExpirationTime = localStorage.getItem('session-expiration');
    sessionExpirationTime = moment.utc(sessionExpirationTime);
    if (moment.utc().add(180, 'seconds') >= sessionExpirationTime) {
      const freshSessionExpiration = await getSessionExpirationTime();
      if (!freshSessionExpiration) {
        dispatch({type: 'RESET'});
        return;
      }
      localStorage.setItem('session-expiration', freshSessionExpiration);
      if (moment.utc().add(180, 'seconds') >= moment.utc(freshSessionExpiration)) {
        countdownInterval.current = setInterval(sessionExpirationCountdownActions, 1000);
        clearInterval(trackSessionInterval.current);
      }
    }
  }, [sessionExpirationCountdownActions]);

  useEffect(() => {
    if (operation === 'active') {
      checkTimeToExpire();
      trackSessionInterval.current = setInterval(checkTimeToExpire, 60000);
      return () => clearInterval(trackSessionInterval.current);
    }
    if (operation === 'expired') {
      localStorage.removeItem('session-expiration');
    }
  }, [operation, checkTimeToExpire]);

  const refreshSession = async () => {
    setInProgress(true);
    let response;
    try {
      response = await indicoAxios.post(sessionRefreshURL());
    } catch (e) {
      return handleAxiosError(e);
    }
    const freshSessionExpiration = response.data.session_expiration;
    if (!freshSessionExpiration) {
      dispatch({type: 'RESET'});
      return false;
    }
    localStorage.setItem('session-expiration', freshSessionExpiration);
    setInProgress(false);
    opened.current = false;
    clearInterval(countdownInterval.current);
    dispatch({type: 'ACTIVATE_SESSION_TIMER'});
    return true;
  };

  const loginAgain = () => {
    dispatch({type: 'RESET'});
    const hash = location.hash;
    location.href = loginURL({next: location.href + hash});
    return true;
  };

  return (
    <Modal
      size="tiny"
      closeIcon={false}
      closeOnDimmerClick={!inProgress}
      closeOnEscape={!inProgress}
      open={operation === 'countdown' || operation === 'expired'}
    >
      <Modal.Header>
        {operation === 'countdown' && (
          <Translate>Your current session is about to expire.</Translate>
        )}
        {operation === 'expired' && <Translate>This session has expired.</Translate>}
      </Modal.Header>
      <Modal.Content>
        {operation === 'countdown' && (
          <>
            <Translate>
              Click on the refresh button if you wish to continue using Indico or you will be logged
              out.
            </Translate>
            <center className="ui large header">{count}</center>
          </>
        )}
        {operation === 'expired' && (
          <Translate>Your current session has expired and you have been logged out.</Translate>
        )}
      </Modal.Content>
      <Modal.Actions>
        {operation === 'countdown' && (
          <Button
            onClick={hardExpiry ? loginAgain : refreshSession}
            disabled={inProgress}
            loading={inProgress}
          >
            <Translate>Refresh</Translate>
          </Button>
        )}
        {operation === 'expired' && (
          <Button onClick={loginAgain} disabled={inProgress} loading={inProgress}>
            <Translate>Login again</Translate>
          </Button>
        )}
        <Button onClick={() => dispatch({type: 'RESET'})} disabled={inProgress}>
          <Translate>Cancel</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

SessionExpirationManager.propTypes = {
  hardExpiry: PropTypes.bool.isRequired,
};

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#session-expiration-root');
  if (root) {
    const sessionExpiration = root.dataset.sessionExpiration;
    const hardExpiry = root.dataset.hardExpiry !== undefined;
    localStorage.setItem('session-expiration', sessionExpiration);
    ReactDOM.render(<SessionExpirationManager hardExpiry={hardExpiry} />, root);
  }
});
