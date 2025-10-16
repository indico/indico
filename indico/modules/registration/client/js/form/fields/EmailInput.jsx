// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import validateEmailURL from 'indico-url:event_registration.check_email';
import validateEmailManagementURL from 'indico-url:event_registration.check_email_management';

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {useSelector} from 'react-redux';
import {Message} from 'semantic-ui-react';

import {FinalInput, validators as v} from 'indico/react/forms';
import {useDebouncedAsyncValidate} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {getUpdateMode} from '../../form_submission/selectors';
import {getStaticData} from '../selectors';

import '../../../styles/regform.module.scss';

export default function EmailInput({htmlId, htmlName, disabled, isRequired}) {
  const isMainEmailField = htmlName === 'email';
  const [message, setMessage] = useState({status: '', message: '', forEmail: ''});
  const isUpdateMode = useSelector(getUpdateMode);
  const {eventId, regformId, registrationUuid, management} = useSelector(getStaticData);
  const [invitationToken, formToken] = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return [params.get('invitation'), params.get('form_token')];
  }, []);
  const url = useMemo(() => {
    const params = {event_id: eventId, reg_form_id: regformId};
    if (invitationToken) {
      params.invitation = invitationToken;
    }
    if (formToken) {
      params.form_token = formToken;
    }
    const fn = management ? validateEmailManagementURL : validateEmailURL;
    return fn(params);
  }, [eventId, regformId, invitationToken, formToken, management]);
  const validateEmail = useDebouncedAsyncValidate(async email => {
    let msg, response;
    email = email.trim();
    if (!email) {
      // we disabled the regular required validator in order for this to always run
      msg = Translate.string('This field is required.');
      setMessage({
        status: 'error',
        forEmail: email,
        message: msg,
      });
      return msg;
    }
    setMessage({
      status: '',
      forEmail: email,
      message: Translate.string('Checking email address...'),
    });
    try {
      response = await indicoAxios.get(url, {
        params: isUpdateMode ? {email, update: registrationUuid} : {email},
      });
    } catch (error) {
      return handleAxiosError(error);
    }
    const data = response.data;
    const name = data.user ? $('<span>', {text: data.user}).html() : null;
    if (data.conflict === 'email-already-registered') {
      msg = Translate.string('There is already a registration with this email address.');
    } else if (data.conflict === 'user-already-registered') {
      msg = Translate.string('The user associated with this email address is already registered.');
    } else if (data.conflict === 'no-user') {
      msg = Translate.string('There is no Indico user associated with this email address.');
    } else if (data.conflict === 'email-other-user-restricted') {
      msg =
        Indico.User.id !== undefined
          ? Translate.string('You cannot use this email address to register.')
          : Translate.string('Please log in using your Indico account to use this email address.');
    } else if (
      data.status === 'error' &&
      (data.conflict === 'email-other-user' || data.conflict === 'email-no-user')
    ) {
      msg = Translate.string('This email address is not associated with your Indico account.');
    } else if (data.conflict === 'email-other-user') {
      msg = (
        <Translate>
          The registration will be re-associated to a different user (
          <Param name="name" wrapper={<strong />} value={name} />
          ).
        </Translate>
      );
    } else if (data.conflict === 'email-no-user') {
      msg = (
        <Translate>
          The registration will be disassociated from the current user (
          <Param name="name" wrapper={<strong />} value={name} />
          ).
        </Translate>
      );
    } else if (data.conflict === 'email-invalid') {
      if (data.email_error === 'undeliverable') {
        msg = Translate.string('The domain used in the email address does not exist.');
      } else {
        msg = Translate.string('This email address is invalid.');
      }
    } else if (!data.user) {
      msg = Translate.string('The registration will not be associated with any Indico account.');
    } else if (data.self) {
      msg = Translate.string('The registration will be associated with your Indico account.');
    } else if (data.same) {
      msg = (
        <Translate>
          The registration will remain associated with the Indico account{' '}
          <Param name="name" wrapper={<strong />} value={name} />.
        </Translate>
      );
    } else {
      msg = (
        <Translate>
          The registration will be associated with the Indico account{' '}
          <Param name="name" wrapper={<strong />} value={name} />.
        </Translate>
      );
    }

    setMessage({status: data.status, message: msg, forEmail: email});
    if (data.status === 'error') {
      return msg;
    }
  }, 250);

  return (
    <FinalInput
      type="email"
      id={htmlId}
      name={htmlName}
      required={isRequired && isMainEmailField ? 'no-validator' : isRequired}
      disabled={disabled}
      validate={isMainEmailField ? validateEmail : isRequired ? v.required : undefined}
      // hide the normal error tooltip if we have an error from our async validation
      hideValidationError={
        isMainEmailField && message.status === 'error' && message.forEmail ? 'message' : false
      }
      loaderWhileValidating
    >
      {isMainEmailField && !!message.forEmail && !!message.message && (
        <Message
          visible
          warning={message.status === 'warning'}
          error={message.status === 'error'}
          positive={message.status === 'ok'}
        >
          {message.message}
        </Message>
      )}
    </FinalInput>
  );
}

EmailInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool.isRequired,
};

EmailInput.defaultProps = {
  disabled: false,
};
