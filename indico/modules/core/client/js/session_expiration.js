// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import loginUrl from 'indico-url:auth.login';
import sessionExpirationUrl from 'indico-url:core.session_expiration';

import moment from 'moment';
import React, {useState, useEffect, useReducer, useRef, useCallback} from 'react';
import ReactDOM from 'react-dom';

import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

const initialState = 'active';

function sessionExpirationReducer(state, action) {
  switch (action.type) {
    case 'SESSION_ACTIVE':
      return 'active';
    case 'SESSION_COUNTDOWN':
      return 'countdown';
    case 'SESSION_EXPIRED':
      return 'expired';
    case 'DEFAULT':
      return 'default';
    default:
      return state;
  }
}

export default function SessionExpirationManager() {
  const [count, setCount] = useState(120);
  const [state, dispatch] = useReducer(sessionExpirationReducer, initialState);
  const trackSessionInterval = useRef(0);
  const countdownInterval = useRef(0);
  const opened = useRef(false);

  const sessionExpirationCountdownActions = useCallback(() => {
    const expiration = localStorage.getItem('session-expiration');
    if (expiration === null) {
      dispatch({type: 'SESSION_EXPIRED'});
      clearInterval(countdownInterval.current);
    }
    const sessionExpiration = moment.utc(expiration);
    const millisecondsLeft = sessionExpiration - moment.utc();
    const counter = Math.ceil(millisecondsLeft / 1000);
    if (counter <= 120 && !opened.current) {
      opened.current = true;
      setCount(counter);
      dispatch({type: 'SESSION_COUNTDOWN'});
    } else if (counter <= 0 && opened.current) {
      dispatch({type: 'SESSION_EXPIRED'});
      clearInterval(countdownInterval.current);
    } else if (counter >= 120 && opened.current) {
      dispatch({type: 'SESSION_ACTIVE'});
      clearInterval(countdownInterval.current);
    }
    setCount(counter);
  }, []);

  const getSessionExpirationTime = async () => {
    let response;
    try {
      response = await indicoAxios.get(sessionExpirationUrl());
    } catch (e) {
      return handleAxiosError(e);
    }
    if (response) {
      return response.data.session_expiration;
    }
  };

  const checkTimeToExpire = useCallback(async () => {
    let sessionExpirationTime = localStorage.getItem('session-expiration');
    sessionExpirationTime = moment.utc(sessionExpirationTime);
    if (moment.utc().add(180, 'seconds') >= sessionExpirationTime) {
      const freshSessionExpiration = await getSessionExpirationTime();
      localStorage.setItem('session-expiration', freshSessionExpiration);
      if (moment.utc().add(180, 'seconds') >= moment.utc(freshSessionExpiration)) {
        countdownInterval.current = setInterval(sessionExpirationCountdownActions, 1000);
        clearInterval(trackSessionInterval.current);
      }
    }
  }, [sessionExpirationCountdownActions]);

  useEffect(() => {
    if (state === 'active') {
      checkTimeToExpire();
      trackSessionInterval.current = setInterval(checkTimeToExpire, 60000);
      return () => clearInterval(trackSessionInterval.current);
    }
    if (state === 'expired') {
      localStorage.removeItem('session-expiration');
    }
  }, [state, checkTimeToExpire]);

  const refreshSession = () => {
    const hash = location.hash;
    location.href = loginUrl({next: location.href + hash});
    return true;
  };

  return (
    <>
      <RequestConfirm
        header={Translate.string('Your current session is about to expire.')}
        confirmText={Translate.string('Refresh')}
        cancelText={Translate.string('Cancel')}
        onClose={() => dispatch({type: 'DEFAULT'})}
        requestFunc={refreshSession}
        open={state === 'countdown'}
      >
        <Translate>
          Click on the refresh button if you wish to continue using Indico or you will be logged
          out.
        </Translate>
        <center className="ui large header">{count}</center>
      </RequestConfirm>
      <RequestConfirm
        header={Translate.string('This Session has expired')}
        confirmText={Translate.string('Ok')}
        cancelText={Translate.string('Cancel')}
        onClose={() => dispatch({type: 'DEFAULT'})}
        requestFunc={() => dispatch({type: 'DEFAULT'})}
        open={state === 'expired'}
      >
        <Translate>Your current session has expired and you have been logged out.</Translate>
      </RequestConfirm>
    </>
  );
}

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('#session-expiration-root');
  if (root) {
    const sessionExpiration = root.dataset.sessionExpiration;
    localStorage.setItem('session-expiration', sessionExpiration);
    ReactDOM.render(<SessionExpirationManager />, root);
  }
});
