// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Message} from 'semantic-ui-react';

import {
  FinalSubmitButton,
  handleSubmitError,
  FinalCheckbox,
  getChangedValues,
} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import ConsentToPublishDropdown from '../components/ConsentToPublishDropdown';
import FormSection from '../form/FormSection';
import {getNestedSections, getStaticData} from '../form/selectors';

import {
  getUpdateMode,
  getModeration,
  getManagement,
  getPublishToParticipants,
  getPublishToPublic,
} from './selectors';

import '../../styles/regform.module.scss';

function EmailNotification() {
  return (
    <Message info style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Email notifications</Translate>
      </Message.Header>
      <div style={{marginTop: 10}}>
        <FinalCheckbox
          label={Translate.string('Send an email notification to the user')}
          name="notify_user"
          toggle
        />
      </div>
    </Message>
  );
}

function ConsentToPublish({
  publishToParticipants,
  publishToPublic,
  maximumConsentToPublish,
  management,
}) {
  const isWarning = publishToParticipants === 'show_all' && publishToPublic === 'show_all';

  return (
    <Message info={!isWarning} warning={isWarning} style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Participant list</Translate>
      </Message.Header>
      {(publishToParticipants === 'show_with_consent' ||
        publishToPublic === 'show_with_consent') && (
        <p>
          {management
            ? Translate.string(
                "Modify the user's consent to being included in the event's list of participants"
              )
            : Translate.string(
                "Specify whether you consent to being included in the event's list of participants"
              )}
        </p>
      )}
      <ConsentToPublishDropdown
        name="consent_to_publish"
        publishToParticipants={publishToParticipants}
        publishToPublic={publishToPublic}
        maximumConsentToPublish={maximumConsentToPublish}
        useFinalForms
      />
    </Message>
  );
}

ConsentToPublish.propTypes = {
  publishToParticipants: PropTypes.oneOf(['hide_all', 'show_with_consent', 'show_all']).isRequired,
  publishToPublic: PropTypes.oneOf(['hide_all', 'show_with_consent', 'show_all']).isRequired,
  maximumConsentToPublish: PropTypes.oneOf(['nobody', 'participants', 'all']).isRequired,
  management: PropTypes.bool.isRequired,
};

export default function RegistrationFormSubmission() {
  const sections = useSelector(getNestedSections);
  const {submitUrl, registrationData, initialValues} = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const isModerated = useSelector(getModeration);
  const isManagement = useSelector(getManagement);
  const publishToParticipants = useSelector(getPublishToParticipants);
  const publishToPublic = useSelector(getPublishToPublic);
  const showConsentToPublish = isManagement
    ? isUpdateMode &&
      registrationData.consent_to_publish !== 'nobody' &&
      (publishToParticipants === 'show_with_consent' || publishToPublic === 'show_with_consent')
    : publishToParticipants !== 'hide_all';

  const onSubmit = async (data, form) => {
    let resp;
    try {
      resp = await indicoAxios.post(submitUrl, isUpdateMode ? getChangedValues(data, form) : data);
    } catch (err) {
      return handleSubmitError(err);
    }

    if (resp.data.redirect) {
      location.href = resp.data.redirect;
    }
  };

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={isUpdateMode ? registrationData : initialValues}
      initialValuesEqual={_.isEqual}
      subscription={{}}
    >
      {fprops => (
        <form onSubmit={fprops.handleSubmit}>
          {sections.map(section => (
            <FormSection key={section.id} {...section} />
          ))}
          <div>
            {isManagement && <EmailNotification />}
            {showConsentToPublish && (
              <ConsentToPublish
                publishToParticipants={publishToParticipants}
                publishToPublic={publishToPublic}
                maximumConsentToPublish={isManagement ? registrationData.consent_to_publish : 'all'}
                management={isManagement}
              />
            )}
            <FinalSubmitButton
              disabledUntilChange={false}
              disabledIfInvalid={false}
              label={
                isUpdateMode
                  ? Translate.string('Modify')
                  : isModerated
                  ? Translate.string('Apply')
                  : Translate.string('Register')
              }
              style={{
                marginTop: 20,
                textAlign: 'right',
              }}
            />
          </div>
        </form>
      )}
    </FinalForm>
  );
}
