// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useFormState} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Button, Form, Label} from 'semantic-ui-react';

import {FinalCheckbox, FinalField, FinalInput, validators as v} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Param, Translate} from 'indico/react/i18n';

import {getPriceFormatter, getItems, getStaticData} from '../selectors';

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

function getAccompanyingPersonCount(value) {
  if (Array.isArray(value)) {
    return value.length;
  }

  if (Number.isFinite(value)) {
    return value;
  }

  return Number(value) || 0;
}

// Gather all accompanying persons field's counts.
function getTotalAccompanyingPersonCount(items, formState) {
  const values = formState.values || {};
  const allAccompanyingPersonFieldNames = Object.values(items)
    .filter(f => f.inputType === 'accompanying_persons' && f.personsCountAgainstLimit)
    .map(apf => apf.htmlName);
  return allAccompanyingPersonFieldNames.reduce(
    (count, field) => count + getAccompanyingPersonCount(values[field]),
    0
  );
}

function calculatePlaces(availablePlaces, maxPersons, personsInCurrentField, items, formState) {
  if (availablePlaces === null) {
    // Field does not count towards registration limit...
    if (!maxPersons) {
      // ...and has no person limit.
      return [null, Infinity];
    } else {
      // ...and has a person limit.
      return [personsInCurrentField, maxPersons];
    }
  } else {
    // Field counts towards registration limit...
    const totalAccompanyingPersonCount = getTotalAccompanyingPersonCount(items, formState);

    if (!maxPersons || maxPersons >= availablePlaces - totalAccompanyingPersonCount) {
      // ...and has no person limit, or its person limit is greater than the registration limit.
      return [totalAccompanyingPersonCount, availablePlaces];
    } else {
      // ...and has a person limit lower than the registration limit.
      return [personsInCurrentField, maxPersons];
    }
  }
}

function getMaxCount(personsInCurrentField, placesUsed, placesLimit) {
  if (placesLimit === Infinity) {
    return null;
  }
  return personsInCurrentField + placesLimit - placesUsed;
}

function clampAnonymousCount(value, maxCount) {
  const normalizedValue = Math.max(0, Math.trunc(Number.isFinite(value) ? value : 0));

  if (maxCount === null) {
    return normalizedValue;
  }

  return Math.min(normalizedValue, maxCount);
}

function AccompanyingPersonsComponent({
  id,
  value,
  disabled,
  onChange,
  price,
  availablePlaces,
  maxPersons,
  isAnonymous,
}) {
  const [operation, setOperation] = useState({type: null, person: null});
  const formatPrice = useSelector(getPriceFormatter);
  const items = useSelector(getItems);
  const formState = useFormState();
  const accompanyingPersonCount = getAccompanyingPersonCount(value);
  const persons = Array.isArray(value) ? value : [];
  const totalPrice = accompanyingPersonCount * price;

  const [placesUsed, placesLimit] = calculatePlaces(
    availablePlaces,
    maxPersons,
    accompanyingPersonCount,
    items,
    formState
  );
  const maxCount = getMaxCount(accompanyingPersonCount, placesUsed, placesLimit);
  const noPlacesLeft = maxCount !== null && accompanyingPersonCount >= maxCount;

  const changeReducer = action => {
    switch (action.type) {
      case 'ADD':
        return [...persons, {id: `new:${nanoid()}`, ...action.person}];
      case 'EDIT':
        return persons.map(p => (p.id === action.person.id ? action.person : p));
      case 'REMOVE':
        return persons.filter(p => p.id !== action.id);
      default:
        return persons;
    }
  };

  const handleAccompanyingPersonAdd = () => {
    setOperation({type: 'ADD', person: null});
  };

  const handleAccompanyingPersonEdit = personId => {
    setOperation({type: 'EDIT', person: persons.find(p => p.id === personId)});
  };

  const handleAccompanyingPersonRemove = personId => {
    onChange(changeReducer({type: 'REMOVE', id: personId}));
  };

  const handleModalClose = () => {
    setOperation({type: null, person: null});
  };

  if (isAnonymous) {
    return (
      <Form.Group styleName="accompanyingpersons-field">
        <div styleName="anonymous">
          <Form.Input
            id={id}
            type="number"
            min="0"
            max={maxCount ?? undefined}
            step="1"
            value={accompanyingPersonCount}
            disabled={disabled}
            onChange={(_, {value: nextValue}) =>
              onChange(clampAnonymousCount(Number(nextValue), maxCount))
            }
            aria-describedby={id ? `${id}-placeslimit` : undefined}
            aria-label={Translate.string('Number of accompanying persons')}
          />
          {!!price && (
            <Label basic pointing="left" styleName="price-tag" size="small">
              <Translate>
                <Param name="price" value={formatPrice(price)} /> (Total:{' '}
                <Param name="totalPrice" value={formatPrice(totalPrice)} />)
              </Translate>
            </Label>
          )}
          {placesLimit !== Infinity && (
            <div id={`${id}-placeslimit`} styleName="places-left">
              <PlacesLeft placesLimit={placesLimit} placesUsed={placesUsed} isEnabled={!disabled} />
            </div>
          )}
        </div>
      </Form.Group>
    );
  }

  return (
    <Form.Group styleName="accompanyingpersons-field">
      <ul>
        {!persons.length && (
          <li styleName="light">
            <Translate>No accompanying persons registered</Translate>
          </li>
        )}
        {persons.map(person => (
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
          type="button"
          onClick={handleAccompanyingPersonAdd}
          disabled={disabled || noPlacesLeft}
          aria-describedby={id ? `${id}-placeslimit` : ''}
        >
          <Translate>Add accompanying person</Translate>
        </Button>
        {!!price && (
          <Label basic pointing="left" styleName="price-tag" size="small">
            <Translate>
              <Param name="price" value={formatPrice(price)} /> (Total:{' '}
              <Param name="totalPrice" value={formatPrice(totalPrice)} />)
            </Translate>
          </Label>
        )}
        {placesLimit !== Infinity && (
          <div id={`${id}-placeslimit`} styleName="places-left">
            <PlacesLeft placesLimit={placesLimit} placesUsed={placesUsed} isEnabled={!disabled} />
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
  id: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        firstName: PropTypes.string.isRequired,
        lastName: PropTypes.string.isRequired,
      })
    ),
  ]).isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  price: PropTypes.number,
  availablePlaces: PropTypes.number,
  maxPersons: PropTypes.number,
  isAnonymous: PropTypes.bool,
};

AccompanyingPersonsComponent.defaultProps = {
  disabled: false,
  price: 0,
  availablePlaces: null,
  maxPersons: null,
  isAnonymous: false,
};

export default function AccompanyingPersonsInput({
  htmlId,
  htmlName,
  disabled,
  price,
  availablePlaces,
  maxPersons,
  isAnonymous,
}) {
  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={AccompanyingPersonsComponent}
      disabled={disabled}
      price={price}
      availablePlaces={availablePlaces}
      maxPersons={maxPersons}
      isAnonymous={isAnonymous}
    />
  );
}

AccompanyingPersonsInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  price: PropTypes.number,
  availablePlaces: PropTypes.number,
  maxPersons: PropTypes.number,
  isAnonymous: PropTypes.bool,
};

AccompanyingPersonsInput.defaultProps = {
  disabled: false,
  price: 0,
  availablePlaces: null,
  maxPersons: null,
  isAnonymous: false,
};

export const accompanyingPersonsSettingsInitialData = {
  maxPersons: 1,
  personsCountAgainstLimit: false,
  isAnonymous: false,
};

export function AccompanyingPersonsSettings({isAnonymousLocked, anonymousLockReason}) {
  const {ticketsForAccompanyingPersons} = useSelector(getStaticData);
  const anonymousDisabledReason = ticketsForAccompanyingPersons
    ? Translate.string(
        'Disable tickets for accompanying persons to enable anonymous accompanying person registration.'
      )
    : anonymousLockReason;

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
        fluid
        format={val => val || ''}
        parse={val => +val || 0}
      />
      <FinalCheckbox
        name="personsCountAgainstLimit"
        label={Translate.string('Accompanying persons count against registration limit')}
      />
      <FinalCheckbox
        name="isAnonymous"
        label={Translate.string('Anonymous accompanying persons')}
        disabled={ticketsForAccompanyingPersons || isAnonymousLocked}
        description={
          <>
            <Translate>
              Collect only the number of accompanying persons instead of their names.
            </Translate>
            <br />
            <Translate>
              Tickets and badge printing are not available for anonymous accompanying persons.
            </Translate>
            {anonymousDisabledReason && (
              <>
                <br />
                {anonymousDisabledReason}
              </>
            )}
          </>
        }
      />
    </>
  );
}

AccompanyingPersonsSettings.propTypes = {
  isAnonymousLocked: PropTypes.bool,
  anonymousLockReason: PropTypes.string,
};

AccompanyingPersonsSettings.defaultProps = {
  isAnonymousLocked: false,
  anonymousLockReason: null,
};
