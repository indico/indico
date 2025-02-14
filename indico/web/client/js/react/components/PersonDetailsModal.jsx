// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchAffiliationURL from 'indico-url:users.api_affiliations';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useForm, useFormState} from 'react-final-form';
import {Form, Message, Header, Button, Icon} from 'semantic-ui-react';

import {FinalComboDropdown, FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useDebouncedAsyncValidate} from 'indico/react/hooks';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import {Param, Translate} from '../i18n';

import './PersonDetailsModal.module.scss';

const debounce = makeAsyncDebounce(250);

const titles = [
  {text: Translate.string('Mr'), value: 'mr'},
  {text: Translate.string('Ms'), value: 'ms'},
  {text: Translate.string('Mrs'), value: 'mrs'},
  {text: Translate.string('Dr'), value: 'dr'},
  {text: Translate.string('Prof'), value: 'prof'},
  {text: Translate.string('Mx'), value: 'mx'},
];

const FinalAffiliationField = ({hasPredefinedAffiliations, ...rest}) => {
  const formState = useFormState();
  const currentAffiliation = formState.values.affiliationMeta;
  const [_affiliationResults, setAffiliationResults] = useState([]);
  const affiliationResults =
    currentAffiliation && !_affiliationResults.find(x => x.id === currentAffiliation.id)
      ? [currentAffiliation, ..._affiliationResults]
      : _affiliationResults;

  const getSubheader = ({city, countryName}) => {
    if (city && countryName) {
      return `${city}, ${countryName}`;
    }
    return city || countryName;
  };

  const affiliationOptions = affiliationResults.map(res => ({
    key: res.id,
    value: res.id,
    meta: res,
    text: `${res.name} `, // XXX: the space allows addition even if the entered text matches a result item
    content: <Header style={{fontSize: 14}} content={res.name} subheader={getSubheader(res)} />,
  }));

  const searchAffiliationChange = async (evt, {searchQuery}) => {
    if (!searchQuery) {
      setAffiliationResults([]);
      return;
    }
    let resp;
    try {
      resp = await debounce(() => indicoAxios.get(searchAffiliationURL({q: searchQuery})));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setAffiliationResults(camelizeKeys(resp.data));
  };

  return hasPredefinedAffiliations ? (
    <FinalComboDropdown
      name="affiliationData"
      options={affiliationOptions}
      fluid
      includeMeta
      additionLabel={Translate.string('Use custom affiliation:') + ' '} // eslint-disable-line prefer-template
      onSearchChange={searchAffiliationChange}
      placeholder={Translate.string('Select an affiliation or add your own')}
      noResultsMessage={Translate.string('Search an affiliation or enter one manually')}
      renderCustomOptionContent={value => (
        <Header content={value} subheader={Translate.string('You entered this option manually')} />
      )}
      {...rest}
    />
  ) : (
    <FinalInput name="affiliation" {...rest} />
  );
};

FinalAffiliationField.propTypes = {
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
};

export default function PersonDetailsModal({
  hasPredefinedAffiliations,
  onSubmit,
  onClose,
  person,
  otherPersons,
  hideEmailField,
  validateEmailUrl,
  requiredPersonFields,
  extraParams,
}) {
  return (
    <FinalModalForm
      id="person-link-details"
      size="tiny"
      onClose={onClose}
      onSubmit={onSubmit}
      header={person ? Translate.string('Edit Person') : Translate.string('Enter Person')}
      submitLabel={Translate.string('Save')}
      initialValues={
        person
          ? {...person, affiliationData: {id: person.affiliationId, text: person.affiliation}}
          : {affiliationData: {id: null, text: ''}, email: ''}
      }
    >
      {/* eslint-disable-next-line eqeqeq */}
      {person && person.userId != null && (
        <Translate as={Message}>
          You are updating details that were originally linked to a user. Please note that its
          identity will remain the same.
        </Translate>
      )}
      <Form.Group widths="equal">
        <FinalDropdown
          name="title"
          label={Translate.string('Title', 'Salutation')}
          fluid
          search
          selection
          options={titles}
          placeholder={Translate.string('None', 'Title (salutation)')}
          required={requiredPersonFields?.includes('title')}
        />
        {!extraParams?.disableAffiliations && (
          <FinalAffiliationField
            label={Translate.string('Affiliation')}
            hasPredefinedAffiliations={hasPredefinedAffiliations}
            required={requiredPersonFields?.includes('affiliation')}
          />
        )}
      </Form.Group>
      <Form.Group widths="equal">
        <FinalInput
          name="firstName"
          label={Translate.string('First Name')}
          required={requiredPersonFields?.includes('first_name')}
        />
        <FinalInput label={Translate.string('Family Name')} name="lastName" required />
      </Form.Group>
      {!hideEmailField && (
        <EmailField
          label={Translate.string('Email')}
          validateUrl={validateEmailUrl}
          person={person}
          otherPersons={otherPersons}
          required={requiredPersonFields?.includes('email')}
        />
      )}
      <Form.Group widths="equal">
        <FinalTextArea
          name="address"
          label={Translate.string('Address')}
          required={requiredPersonFields?.includes('address')}
        />
        <FinalInput
          name="phone"
          label={Translate.string('Telephone')}
          required={requiredPersonFields?.includes('phone')}
        />
      </Form.Group>
    </FinalModalForm>
  );
}

PersonDetailsModal.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  person: PropTypes.object,
  otherPersons: PropTypes.array,
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
  hideEmailField: PropTypes.bool,
  validateEmailUrl: PropTypes.string,
  requiredPersonFields: PropTypes.array,
  extraParams: PropTypes.object,
};

PersonDetailsModal.defaultProps = {
  person: undefined,
  otherPersons: [],
  hideEmailField: false,
  validateEmailUrl: null,
  requiredPersonFields: [],
  extraParams: {},
};

function EmailField({validateUrl, person, otherPersons, ...rest}) {
  let response, msg;
  const [message, setMessage] = useState({status: '', message: ''});
  const form = useForm();
  const [user, setUser] = useState(null);
  const [eventPerson, setEventPerson] = useState(null);
  const isUpdate = !!person;

  const validateEmail = useDebouncedAsyncValidate(async email => {
    form.change('personId', person?.personId);
    form.change('avatarURL', null);
    email = email.trim();

    if (email === '' || email === person?.email) {
      setMessage({status: '', message: ''});
      return;
    }

    // Prevent adding the same person twice
    if (otherPersons.some(p => p.email === email)) {
      msg = Translate.string('There is already a person with this email in the list.');
      setMessage({
        status: 'error',
        message: msg,
      });
      return msg;
    }

    setMessage({
      status: '',
      message: Translate.string('Checking email address...'),
    });

    try {
      response = await indicoAxios.get(validateUrl, {
        params: {email},
      });
    } catch (error) {
      return handleAxiosError(error);
    }

    const data = camelizeKeys(response.data);
    const {status, conflict} = data;
    setUser(data.user);
    setEventPerson(data.eventPerson);

    // A user can have multiple emails associated with their account.
    // Check already added persons if there is any with the same userId
    if (data.user) {
      const existingPerson = otherPersons.find(p => data.user.id === p.userId);
      if (existingPerson) {
        msg = (
          <Translate>
            This email is associated with{' '}
            <Param name="name" wrapper={<strong />} value={existingPerson.name} /> who is already in
            the list.
          </Translate>
        );
        setMessage({
          status: 'error',
          message: msg,
        });
        return msg;
      }
    }

    if (conflict === 'person-already-exists' || conflict === 'user-and-person-already-exists') {
      form.change('personId', data.eventPerson.id);
    }

    // Load the user's avatar
    if (conflict === 'user-already-exists' || conflict === 'user-and-person-already-exists') {
      form.change('avatarURL', data.user.avatarURL);
    }

    if (
      conflict === 'user-already-exists' ||
      conflict === 'person-already-exists' ||
      conflict === 'user-and-person-already-exists'
    ) {
      const obj = data.eventPerson || data.user;
      const name = obj.fullName || obj.name;
      if (isUpdate) {
        msg = (
          <Translate>
            This email is already used by <Param name="name" wrapper={<strong />} value={name} />.
            You can update the form with their information.
          </Translate>
        );
      } else {
        msg = (
          <Translate>
            This email is already used by <Param name="name" wrapper={<strong />} value={name} />.
            You can add the person directly or update the form with their information.
          </Translate>
        );
      }
    } else if (conflict === 'email-invalid') {
      if (data.emailError === 'undeliverable') {
        msg = Translate.string('The domain used in the email address does not exist.');
      } else {
        msg = Translate.string('This email address is invalid.');
      }
    } else if (status === 'ok') {
      msg = Translate.string('This email is currently not linked to this event.');
    }

    setMessage({status, message: msg});
    if (status === 'error') {
      return msg;
    }
  }, 250);

  const onClick = async () => {
    if (user) {
      form.change('userId', user.id);
    }
    const obj = eventPerson || user;
    form.change('address', obj.address);
    form.change('name', obj.fullName || obj.name);
    form.change('firstName', obj.firstName);
    form.change('lastName', obj.lastName);
    form.change('title', obj.title);
    form.change('phone', obj.phone);
    form.change('affiliationData', {id: obj.affiliationId, text: obj.affiliation});
    form.change('affiliationMeta', obj.affiliationMeta);
  };

  const emailBtns = (
    <div styleName="email-buttons">
      {!isUpdate && (
        <Button icon type="submit" primary size="tiny" labelPosition="right" onClick={onClick}>
          <Icon name="add" />
          <Translate>Add</Translate>
        </Button>
      )}
      <Button icon type="button" size="tiny" labelPosition="right" onClick={onClick}>
        <Icon name="sync" />
        <Translate>Update</Translate>
      </Button>
    </div>
  );

  const showEmailBtns = message.status !== 'error' && (!!user || !!eventPerson);

  return (
    <FinalInput
      type="email"
      name="email"
      validate={validateUrl ? validateEmail : undefined}
      // hide the normal error tooltip if we have an error from our async validation
      hideValidationError={message.status === 'error' ? 'message' : false}
      loaderWhileValidating
      {...rest}
    >
      {!!message.message && (
        <Message
          visible
          error={message.status === 'error'}
          warning={message.status === 'warning'}
          positive={message.status === 'ok'}
        >
          <div>{message.message}</div>
          {showEmailBtns && emailBtns}
        </Message>
      )}
    </FinalInput>
  );
}

EmailField.propTypes = {
  validateUrl: PropTypes.string,
  person: PropTypes.object,
  otherPersons: PropTypes.array.isRequired,
};

EmailField.defaultProps = {
  person: null,
  validateUrl: null,
};
