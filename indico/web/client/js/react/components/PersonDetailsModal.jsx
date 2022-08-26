// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import validateEmailURL from 'indico-url:events.check_email';
import searchAffiliationURL from 'indico-url:users.api_affiliations';

import PropTypes from 'prop-types';
import React, {useState, useMemo} from 'react';
import {useForm, useFormState} from 'react-final-form';
import {Form, Message, Header, Button} from 'semantic-ui-react';

import {FinalComboDropdown, FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useDebouncedAsyncValidate} from 'indico/react/hooks';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import {Param, Translate} from '../i18n';

const debounce = makeAsyncDebounce(250);

const titles = [
  {text: Translate.string('Mr'), value: 'mr'},
  {text: Translate.string('Ms'), value: 'ms'},
  {text: Translate.string('Mrs'), value: 'mrs'},
  {text: Translate.string('Dr'), value: 'dr'},
  {text: Translate.string('Prof'), value: 'prof'},
  {text: Translate.string('Mx'), value: 'mx'},
];

const FinalAffiliationField = ({hasPredefinedAffiliations}) => {
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
    />
  ) : (
    <FinalInput name="affiliation" />
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
  eventId,
  otherPersons,
  hideEmailField,
}) {
  const shouldValidateEmail = eventId !== null;
  const emailValidateUrl = useMemo(() => validateEmailURL({event_id: eventId}), [eventId]);
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
        <Form.Field>
          <Translate as="label">Title</Translate>
          <FinalDropdown name="title" fluid search selection options={titles} />
        </Form.Field>
        <Form.Field>
          <Translate as="label">Affiliation</Translate>
          <FinalAffiliationField hasPredefinedAffiliations={hasPredefinedAffiliations} />
        </Form.Field>
      </Form.Group>
      <Form.Group widths="equal">
        <Form.Field>
          <Translate as="label">First Name</Translate>
          <FinalInput name="firstName" />
        </Form.Field>
        <Form.Field>
          <Translate as="label">Family Name</Translate>
          <FinalInput name="lastName" required />
        </Form.Field>
      </Form.Group>
      {!hideEmailField && (
        <Form.Field>
          <Translate as="label">Email</Translate>
          <EmailField
            shouldValidate={shouldValidateEmail}
            validateUrl={emailValidateUrl}
            person={person}
            otherPersons={otherPersons}
          />
        </Form.Field>
      )}
      <Form.Group widths="equal">
        <Form.Field>
          <Translate as="label">Address</Translate>
          <FinalTextArea name="address" />
        </Form.Field>
        <Form.Field>
          <Translate as="label">Telephone</Translate>
          <FinalInput name="phone" />
        </Form.Field>
      </Form.Group>
    </FinalModalForm>
  );
}

PersonDetailsModal.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  person: PropTypes.object,
  eventId: PropTypes.number,
  otherPersons: PropTypes.array,
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
  hideEmailField: PropTypes.bool,
};

PersonDetailsModal.defaultProps = {
  person: undefined,
  eventId: null,
  otherPersons: [],
  hideEmailField: false,
};

function EmailField({shouldValidate, validateUrl, person, otherPersons}) {
  let response, msg;
  const [message, setMessage] = useState({status: '', message: ''});
  const form = useForm();
  const [user, setUser] = useState(null);
  const [eventPerson, setEventPerson] = useState(null);
  const isUpdate = !!person;

  const validateEmail = useDebouncedAsyncValidate(async email => {
    form.change('personId', person?.personId);
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

    const {data} = response;
    const {status, conflict} = data;
    setUser(data.user);
    setEventPerson(data.event_person);

    if (conflict === 'person-already-exists' || conflict === 'user-and-person-already-exists') {
      form.change('personId', data.event_person.id);
    }

    if (conflict === 'user-already-exists' || conflict === 'user-and-person-already-exists') {
      form.change('avatarURL', data.user.avatar_url);
    }

    if (
      conflict === 'user-already-exists' ||
      conflict === 'person-already-exists' ||
      conflict === 'user-and-person-already-exists'
    ) {
      const obj = data.event_person || data.user;
      const name = obj.full_name || obj.name;
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
      if (data.email_error === 'undeliverable') {
        msg = Translate.string('The domain used in the email address does not exist.');
      } else {
        msg = Translate.string('This email address is invalid.');
      }
    } else if (status === 'ok') {
      msg = Translate.string('This email is currently not linked to this event.');
    }

    setMessage({status, message: msg});
    if (status === 'error') {
      setMessage({status, message: msg});
      return msg;
    }
  }, 250);

  const onClick = async () => {
    const obj = eventPerson || user;
    form.change('address', obj.address);
    form.change('firstName', obj.first_name);
    form.change('lastName', obj.last_name);
    form.change('title', obj.title);
    form.change('phone', obj.phone);
    form.change('affiliationData', {id: obj.affiliation_id, text: obj.affiliation});
    form.change('affiliationMeta', obj.affiliation_meta);
  };

  const emailBtn = (
    <div style={{textAlign: 'right'}}>
      {!isUpdate && (
        <Button type="submit" primary size="tiny" onClick={onClick}>
          <Translate>Add</Translate>
        </Button>
      )}
      <Button type="button" size="tiny" onClick={onClick}>
        <Translate>Update</Translate>
      </Button>
    </div>
  );

  return (
    <FinalInput
      type="email"
      name="email"
      validate={shouldValidate ? validateEmail : undefined}
      // hide the normal error tooltip if we have an error from our async validation
      hideValidationError={message.status === 'error' ? 'message' : false}
      loaderWhileValidating
    >
      {!!message.message && (
        <Message
          visible
          error={message.status === 'error'}
          warning={message.status === 'warning'}
          positive={message.status === 'ok'}
        >
          <div>{message.message}</div>
          {(!!user || !!eventPerson) && emailBtn}
        </Message>
      )}
    </FinalInput>
  );
}

EmailField.propTypes = {
  validateUrl: PropTypes.string.isRequired,
  shouldValidate: PropTypes.bool.isRequired,
  person: PropTypes.object,
  otherPersons: PropTypes.array.isRequired,
};

EmailField.defaultProps = {
  person: null,
};
