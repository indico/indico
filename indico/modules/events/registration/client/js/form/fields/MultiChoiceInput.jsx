// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Form} from 'semantic-ui-react';

import {FinalCheckbox, FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {Choices, choiceShape} from './ChoicesSetup';

import '../../../styles/regform.module.scss';

export default function MultiChoiceInput({
  htmlName,
  disabled,
  choices,
  withExtraSlots,
  title,
  isRequired,
}) {
  // TODO: billable/price
  // TODO: places left
  // TODO: set value as `{uuid: places}` (when adding final-form integration)
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices
  const currency = useSelector(getCurrency);
  const [value, setValue] = useState({});

  const makeHandleChange = choice => evt => {
    setValue(prev => ({...prev, [choice.id]: +evt.target.checked}));
  };
  const makeHandleSlotsChange = choice => evt => {
    setValue(prev => ({...prev, [choice.id]: +evt.target.value}));
  };

  return (
    <Form.Field required={isRequired} styleName="field">
      <label>{title}</label>
      <ul styleName="radio-group">
        {choices.map(choice => (
          <li key={choice.id}>
            <input
              type="checkbox"
              name={htmlName}
              id={`${htmlName}-${choice.id}`}
              value={choice.id}
              disabled={!choice.isEnabled || disabled}
              checked={!!value[choice.id]}
              onChange={makeHandleChange(choice)}
            />{' '}
            <label htmlFor={`${htmlName}-${choice.id}`}>
              {choice.caption} {!!choice.price && `(${choice.price} ${currency})`}
            </label>
            {!!value[choice.id] && withExtraSlots && choice.maxExtraSlots > 0 && (
              <>
                <select
                  name={`${htmlName}-${choice.id}-extra`}
                  disabled={disabled}
                  value={value[choice.id]}
                  onChange={makeHandleSlotsChange(choice)}
                >
                  {_.range(1, choice.maxExtraSlots + 2).map(i => (
                    <option key={i} value={i}>
                      {i}
                    </option>
                  ))}
                </select>
                {!!choice.price && (
                  <span styleName="price">
                    Total: {(choice.extraSlotsPay ? value[choice.id] : 1) * choice.price} {currency}
                  </span>
                )}
              </>
            )}
          </li>
        ))}
      </ul>
    </Form.Field>
  );
}

MultiChoiceInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  // TODO: placesUsed, captions - only needed once we deal with real data
};

MultiChoiceInput.defaultProps = {
  disabled: false,
  withExtraSlots: false,
};

export const multiChoiceSettingsInitialData = {
  choices: [],
  withExtraSlots: false,
};

export function MultiChoiceSettings() {
  return (
    <>
      <FinalCheckbox name="withExtraSlots" label={Translate.string('Enable extra slots')} />
      <Field name="withExtraSlots" subscription={{value: true}}>
        {({input: {value: withExtraSlots}}) => (
          <FinalField
            name="choices"
            label={Translate.string('Choices')}
            component={Choices}
            withExtraSlots={withExtraSlots}
            isEqual={_.isEqual}
            required
          />
        )}
      </Field>
    </>
  );
}
