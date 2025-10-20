// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import privacyNoticeURL from 'indico-url:events.display_privacy';

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
import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {getPluginObjects, renderPluginComponents} from 'indico/utils/plugins';

import ConsentToPublishDropdown from '../components/ConsentToPublishDropdown';
import ConditionalFieldsController from '../form/ConditionalFieldsController';
import FormErrorList from '../form/FormErrorList';
import FormSection from '../form/FormSection';
import {
  getHiddenItemHTMLNames,
  getHiddenItemsInitialized,
  getNestedSections,
  getStaticData,
} from '../form/selectors';

import {
  getUpdateMode,
  getModeration,
  getManagement,
  getPublishToParticipants,
  getPublishToPublic,
} from './selectors';

import '../../styles/regform.module.scss';

function PrivacyPolicy({url}) {
  const label = (
    <Translate>
      I have read and agree to the{' '}
      <Param name="url" wrapper={<a href={url} target="_blank" rel="noreferrer" />}>
        Privacy policy
      </Param>
    </Translate>
  );

  return (
    <Message info style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Privacy Policy</Translate>
      </Message.Header>
      <Form as="div" style={{marginTop: 10}}>
        <FinalCheckbox required label={label} name="agreed_to_privacy_policy" showAsToggle />
      </Form>
    </Message>
  );
}

PrivacyPolicy.propTypes = {
  url: PropTypes.string.isRequired,
};

function ManagementOptions({isUpdateMode}) {
  return (
    <Message info style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Management Options</Translate>
      </Message.Header>
      <div>
        <FinalCheckbox
          fieldProps={{style: {marginTop: 10}}}
          label={Translate.string('Send an email notification to the user')}
          name="notify_user"
          showAsToggle
        />
        {!isUpdateMode && (
          <FinalCheckbox
            fieldProps={{style: {marginTop: 10}}}
            label={Translate.string('Ignore field requirements for custom fields')}
            name="override_required"
            showAsToggle
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
    eventId,
    submitUrl,
    registrationData,
    initialValues,
    captchaRequired,
    captchaSettings,
    policyAgreementRequired,
  } = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const isModerated = useSelector(getModeration);
  const isManagement = useSelector(getManagement);
  const publishToParticipants = useSelector(getPublishToParticipants);
  const publishToPublic = useSelector(getPublishToPublic);
  const showConsentToPublish = !isManagement && publishToParticipants !== 'hide_all';
  const hiddenItemHTMLNames = useSelector(getHiddenItemHTMLNames);
  const hiddenItemsInitialized = useSelector(getHiddenItemsInitialized);

  const onSubmit = async (data, form) => {
    // There is no need to store whether the user accepted the privacy policy
    // as it is not possible to submit the form without accepting it.
    data = _.omit(data, 'agreed_to_privacy_policy');
    // Do not send data for hidden fields; they are cleared server-side.
    data = _.omit(data, hiddenItemHTMLNames);
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
          <ConditionalFieldsController />
          {hiddenItemsInitialized && (
            // avoid rendering the form until the conditional fields controller had the chance
            // to run, to avoid initially-hidden fields from showing up for a short moment on load
            <>
              {renderPluginComponents('regformBeforeSections')}
              {sections.map(section => (
                <FormSection key={section.id} {...section} />
              ))}
              {renderPluginComponents('regformAfterSections')}
            </>
          )}
          <div>
            {isManagement && <ManagementOptions isUpdateMode={isUpdateMode} />}
            {showConsentToPublish && (
              <ConsentToPublish
                publishToParticipants={publishToParticipants}
                publishToPublic={publishToPublic}
              />
            )}
            {captchaRequired && <Captcha settings={captchaSettings} />}
            {!isManagement && !isUpdateMode && policyAgreementRequired && (
              <PrivacyPolicy url={privacyNoticeURL({event_id: eventId})} />
            )}
            <FormErrorList />
            <FinalSubmitButton
              disabledUntilChange={false}
              disabledIfInvalid={false}
              label={
                isUpdateMode
                  ? Translate.string('Modify')
                  : isModerated
                    ? Translate.string('Apply', 'Registration')
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
