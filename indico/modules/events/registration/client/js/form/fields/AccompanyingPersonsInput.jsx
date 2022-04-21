// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Button, Form, Label} from 'semantic-ui-react';

import {FinalCheckbox, FinalField, FinalInput, validators as v} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../selectors';

import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';

function AccompanyingPersonModal({value, header, onSubmit, onClose}) {
  return (
    <FinalModalForm
      id="accompanyingperson-form"
      onSubmit={onSubmit}
      onClose={onClose}
      initialValues={value}
      header={header}
    >
      <FinalInput name="firstName" label={Translate.string('First Name')} required autoFocus />
      <FinalInput name="lastName" label={Translate.string('Last Name')} required />
    </FinalModalForm>
  );
}

AccompanyingPersonModal.propTypes = {
  value: PropTypes.shape({
    id: PropTypes.string.isRequired,
    firstName: PropTypes.string.isRequired,
    lastName: PropTypes.string.isRequired,
  }),
  header: PropTypes.string.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

AccompanyingPersonModal.defaultProps = {
  value: {
    id: null,
    firstName: null,
    lastName: null,
  },
};

function AccompanyingPersonsComponent({value, disabled, onChange, price, availablePlaces}) {
  const [operation, setOperation] = useState({type: null, person: null});
  const currency = useSelector(getCurrency);
  const totalPrice = (value.length * price).toFixed(2);

  const changeReducer = action => {
    switch (action.type) {
      case 'ADD':
        return [...value, {id: nanoid(), ...action.person}];
      case 'EDIT':
        return [...value.map(p => (p.id === action.person.id ? action.person : p))];
      case 'REMOVE':
        return [...value.filter(p => p.id !== action.id)];
    }
  };

  const handleAccompanyingPersonAdd = () => {
    setOperation({type: 'ADD', person: null});
  };

  const handleAccompanyingPersonEdit = id => {
    setOperation({type: 'EDIT', person: value.find(p => p.id === id)});
  };

  const handleAccompanyingPersonRemove = id => {
    onChange(changeReducer({type: 'REMOVE', id}));
  };

  const handleModalClose = () => {
    setOperation({type: null, person: null});
  };

  return (
    <Form.Group styleName="accompanyingpersons-field">
      <ul>
        {!value.length && (
          <li styleName="light">
            <Translate>No accompanying persons registered</Translate>
          </li>
        )}
        {value.map(person => (
          <li key={person.id}>
            <span>
              {person.firstName} {person.lastName}
            </span>
            <div styleName="actions">
              <a
                className="icon-edit"
                title={Translate.string('Edit this person')}
                onClick={() => handleAccompanyingPersonEdit(person.id)}
              />
              <a
                className="icon-remove"
                title={Translate.string('Remove this person')}
                onClick={() => handleAccompanyingPersonRemove(person.id)}
              />
            </div>
          </li>
        ))}
      </ul>
      <div styleName="summary">
        <Button
          size="small"
          onClick={handleAccompanyingPersonAdd}
          disabled={disabled || value.length >= availablePlaces}
        >
          <Translate>Add accompanying person</Translate>
        </Button>
        {!!price && (
          <Label basic pointing="left" styleName="price-tag" size="small">
            {price.toFixed(2)} {currency} (Total: {totalPrice} {currency})
          </Label>
        )}
        {availablePlaces !== null && (
          <div styleName="places-left">
            <PlacesLeft
              placesLimit={availablePlaces}
              placesUsed={value.length}
              isEnabled={!disabled}
            />
          </div>
        )}
      </div>
      {['ADD', 'EDIT'].includes(operation.type) && (
        <AccompanyingPersonModal
          header={
            operation.type === 'EDIT'
              ? Translate.string('Edit accompanying person')
              : Translate.string('Add accompanying person')
          }
          onSubmit={formData => {
            onChange(changeReducer({type: operation.type, person: formData}));
            handleModalClose();
          }}
          value={operation.person}
          onClose={handleModalClose}
        />
      )}
    </Form.Group>
  );
}

AccompanyingPersonsComponent.propTypes = {
  value: PropTypes.arrayOf(
    PropTypes.shape({
      firstName: PropTypes.string.isRequired,
      lastName: PropTypes.string.isRequired,
    })
  ).isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  price: PropTypes.number,
  availablePlaces: PropTypes.number,
};

AccompanyingPersonsComponent.defaultProps = {
  disabled: false,
  price: 0,
  availablePlaces: null,
};

export default function AccompanyingPersonsInput({htmlName, disabled, price, availablePlaces}) {
  return (
    <FinalField
      name={htmlName}
      component={AccompanyingPersonsComponent}
      disabled={disabled}
      price={price}
      availablePlaces={availablePlaces}
    />
  );
}

AccompanyingPersonsInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  price: PropTypes.number,
  availablePlaces: PropTypes.number,
};

AccompanyingPersonsInput.defaultProps = {
  disabled: false,
  price: 0,
  availablePlaces: null,
};

export function AccompanyingPersonsSettings() {
  return (
    <>
      <FinalInput
        name="maxPersons"
        type="number"
        label={Translate.string('Maximum per registrant')}
        placeholder={Translate.string('No maximum')}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
        defaultValue="1"
        fluid
        format={val => val || ''}
        parse={val => +val || 0}
      />
      <FinalCheckbox
        name="personsCountAgainstLimit"
        label={Translate.string('Accompanying persons count against registration limit')}
      />
    </>
  );
}
