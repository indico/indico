// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchAffiliationURL from 'indico-url:users.api_affiliations';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form, Message, Header} from 'semantic-ui-react';

import {FinalComboDropdown, FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import {Translate} from '../i18n';

const debounce = makeAsyncDebounce(250);

const titles = [
  {text: Translate.string('Mr'), value: 'mr'},
  {text: Translate.string('Ms'), value: 'ms'},
  {text: Translate.string('Mrs'), value: 'mrs'},
  {text: Translate.string('Dr'), value: 'dr'},
  {text: Translate.string('Prof'), value: 'prof'},
  {text: Translate.string('Mx'), value: 'mx'},
];

const FinalAffiliationField = ({hasPredefinedAffiliations, currentAffiliation}) => {
  const [_affiliationResults, setAffiliationResults] = useState([]);
  const affiliationResults =
    currentAffiliation && !_affiliationResults.find(x => x.id === currentAffiliation.id)
      ? [currentAffiliation, ..._affiliationResults]
      : _affiliationResults;

  const getSubheader = ({city, country_name: countryName}) => {
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
    setAffiliationResults(resp.data);
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
  currentAffiliation: PropTypes.object,
};

FinalAffiliationField.defaultProps = {
  currentAffiliation: null,
};

export default function PersonDetailsModal({
  hasPredefinedAffiliations,
  onSubmit,
  onClose,
  person,
  hideEmailField,
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
          : {affiliationData: {id: null, text: ''}}
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
          <FinalAffiliationField
            currentAffiliation={person?.affiliationMeta}
            hasPredefinedAffiliations={hasPredefinedAffiliations}
          />
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
          <FinalInput name="email" required />
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
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
  hideEmailField: PropTypes.bool,
};

PersonDetailsModal.defaultProps = {
  person: undefined,
  hideEmailField: false,
};
