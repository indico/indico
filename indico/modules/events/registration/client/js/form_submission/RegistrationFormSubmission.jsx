// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Form, Message} from 'semantic-ui-react';

import {Captcha} from 'indico/react/components';
import {
  FinalSubmitButton,
  handleSubmitError,
  FinalCheckbox,
  getChangedValues,
} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {getPluginObjects, renderPluginComponents} from 'indico/utils/plugins';

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

function ManagementOptions({isUpdateMode}) {
  return (
    <Message info style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Management Options</Translate>
      </Message.Header>
      <div>
        <FinalCheckbox
          style={{marginTop: 10}}
          label={Translate.string('Send an email notification to the user')}
          name="notify_user"
          toggle
        />
        {!isUpdateMode && (
          <FinalCheckbox
            style={{marginTop: 10}}
            label={Translate.string('Ignore field requirements for custom fields')}
            name="override_required"
            toggle
          />
        )}
      </div>
    </Message>
  );
}
ManagementOptions.propTypes = {
  isUpdateMode: PropTypes.bool.isRequired,
};

function ConsentToPublish({publishToParticipants, publishToPublic}) {
  const isWarning = publishToParticipants === 'show_all' && publishToPublic === 'show_all';
  return (
    <Message info={!isWarning} warning={isWarning} style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Participant list</Translate>
      </Message.Header>
      {(publishToParticipants === 'show_with_consent' ||
        publishToPublic === 'show_with_consent') && (
        <p>
          <Translate>
            Specify whether you consent to being included in the event's list of participants
          </Translate>
        </p>
      )}
      <Form as="div">
        <ConsentToPublishDropdown
          name="consent_to_publish"
          publishToParticipants={publishToParticipants}
          publishToPublic={publishToPublic}
          useFinalForms
        />
      </Form>
    </Message>
  );
}

ConsentToPublish.propTypes = {
  publishToParticipants: PropTypes.oneOf(['hide_all', 'show_with_consent', 'show_all']).isRequired,
  publishToPublic: PropTypes.oneOf(['hide_all', 'show_with_consent', 'show_all']).isRequired,
};

export default function RegistrationFormSubmission() {
  const sections = useSelector(getNestedSections);
  const {
    submitUrl,
    registrationData,
    initialValues,
    captchaRequired,
    captchaSettings,
  } = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const isModerated = useSelector(getModeration);
  const isManagement = useSelector(getManagement);
  const publishToParticipants = useSelector(getPublishToParticipants);
  const publishToPublic = useSelector(getPublishToPublic);
  const showConsentToPublish = !isManagement && publishToParticipants !== 'hide_all';

  const onSubmit = async (data, form) => {
    let resp;
    const formData = isUpdateMode ? getChangedValues(data, form, ['notify_user']) : data;
    try {
      resp = await indicoAxios.post(submitUrl, formData);
    } catch (err) {
      return handleSubmitError(err);
    }

    if (resp.data.redirect) {
      location.href = resp.data.redirect;
      // never finish submitting to avoid fields being re-enabled
      await new Promise(() => {});
    }
  };

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={isUpdateMode ? registrationData : initialValues}
      initialValuesEqual={_.isEqual}
      subscription={{}}
      decorators={getPluginObjects('regformFormDecorators')}
    >
      {fprops => (
        <form onSubmit={fprops.handleSubmit}>
          {sections.map(section => (
            <FormSection key={section.id} {...section} />
          ))}
          {renderPluginComponents('regformAfterSections')}
          <div>
            {isManagement && <ManagementOptions isUpdateMode={isUpdateMode} />}
            {showConsentToPublish && (
              <ConsentToPublish
                publishToParticipants={publishToParticipants}
                publishToPublic={publishToPublic}
              />
            )}
            {captchaRequired && <Captcha settings={captchaSettings} />}
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
