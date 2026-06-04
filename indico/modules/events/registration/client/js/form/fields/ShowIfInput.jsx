// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Field, useForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Icon, Popup} from 'semantic-ui-react';

import {FinalDropdown} from 'indico/react/forms';
import {Fieldset, unsortedArraysEqual} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {showIfFieldDisabled} from '../../form_setup/selectors';
import {getItems, getNestedSections} from '../selectors';

import {getFieldRegistry} from './registry';

export function ShowIfInput({fieldId: thisFieldId}) {
  const fields = useSelector(getItems);
  const sections = useSelector(getNestedSections);
  const fieldRegistry = getFieldRegistry();
  const form = useForm();
  const isShowIfFieldDisabled = useSelector(state => showIfFieldDisabled(state, thisFieldId));

  const choices = sections.flatMap(section =>
    section.items
      .filter(({id, inputType}) => id !== thisFieldId && !!fieldRegistry[inputType].showIfOptions)
      .map(({title, id: fieldId, isEnabled}) => ({
        value: fieldId,
        text: `${section.title} » ${title}`,
        disabled: !isEnabled,
      }))
  );

  return (
    <Fieldset legend={Translate.string('Show if')}>
      {isShowIfFieldDisabled && (
        <Popup trigger={<Icon name="warning sign" color="orange" />}>
          <Translate>
            The conditional field set to display this field is currently disabled and not in effect.
            You may either re-enable the previous field or select another field to use for the
            condition below.
          </Translate>
        </Popup>
      )}
      <FinalDropdown
        name="showIfFieldId"
        /* i18n: Form field */
        label={Translate.string('Field')}
        placeholder={Translate.string('Select field...')}
        options={choices}
        closeOnChange
        selection
        allowNull
        nullIfEmpty
        onChange={() => {
          form.change('showIfFieldValues', null);
        }}
      />
      <Field name="showIfFieldId" subscription={{value: true}}>
        {({input: {value: selectedFieldId}}) => {
          if (!selectedFieldId) {
            return null;
          }
          const field = fields[selectedFieldId];
          const options = fieldRegistry[field.inputType].showIfOptions(field);
          if (!options) {
            throw new Error(`Input ${field.inputType} field has no options defined`);
          }

          // XXX maybe this is wrong, single choice inputs could be optional but enable some field
          // for either its options are chosen...
          const isMultipleChoice = options.length > 2;
          return (
            <FinalDropdown
              required
              name="showIfFieldValues"
              label={
                isMultipleChoice ? Translate.string('Has values') : Translate.string('Has value')
              }
              placeholder={Translate.string('Select values...')}
              options={options}
              multiple={isMultipleChoice}
              parse={value => (isMultipleChoice ? value : [value])}
              format={value => {
                if (isMultipleChoice) {
                  return value ?? [];
                } else {
                  return value ? value[0] : null;
                }
              }}
              isEqual={unsortedArraysEqual}
              closeOnChange
              selection
              allowNull
            />
          );
        }}
      </Field>
    </Fieldset>
  );
}

ShowIfInput.propTypes = {
  fieldId: PropTypes.number,
};

ShowIfInput.defaultProps = {
  fieldId: null, // null when adding new field
};
