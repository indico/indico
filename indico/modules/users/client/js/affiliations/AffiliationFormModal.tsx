// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {FormApi} from 'final-form';
import React from 'react';
import {Accordion, Form, Loader} from 'semantic-ui-react';

import {FinalInput} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';
import {getPluginObjects} from 'indico/utils/plugins';

import {FinalStringListField} from './StringListField';
import {AffiliationFormValues} from './types';

const defaultValues = {
  name: '',
  altNames: [],
  street: '',
  postcode: '',
  city: '',
  countryCode: '',
};

export default function AffiliationFormModal({
  mode,
  initialValues = {},
  onSubmit,
  onClose,
  loading = false,
}: {
  mode: 'create' | 'edit';
  initialValues?: Partial<AffiliationFormValues>;
  onSubmit: (
    data: AffiliationFormValues,
    form: FormApi<AffiliationFormValues>
  ) => void | Promise<void>;
  onClose: () => void;
  loading?: boolean;
}): JSX.Element {
  const isEdit = mode === 'edit';
  const header = isEdit
    ? Translate.string('Edit affiliation')
    : Translate.string('Add affiliation');
  const submitLabel = isEdit ? Translate.string('Save') : Translate.string('Add');

  const sections = [
    {
      key: 'address',
      title: Translate.string('Address'),
      content: {
        content: (
          <>
            <Form.Group widths="equal">
              <FinalInput name="street" label={Translate.string('Street')} />
              <FinalInput name="postcode" label={Translate.string('Postal Code')} />
            </Form.Group>
            <Form.Group widths="equal">
              <FinalInput name="city" label={Translate.string('City')} />
              <FinalInput name="countryCode" label={Translate.string('Country code')} />
            </Form.Group>
          </>
        ),
      },
    },
    ...getPluginObjects('affiliation-form-sections').flat(),
  ];

  return (
    <FinalModalForm
      id="affiliation-form-modal"
      size="small"
      header={header}
      onClose={onClose}
      onSubmit={onSubmit}
      submitLabel={submitLabel}
      initialValues={{...defaultValues, ...initialValues}}
      disabledUntilChange
    >
      {loading ? (
        <Loader inline="centered" active />
      ) : (
        <>
          <FinalInput name="name" label={Translate.string('Name')} required />
          <FinalStringListField
            name="altNames"
            label={Translate.string('Alternative names')}
            placeholder={Translate.string('Type a name and press Enter to add')}
          />
          <Accordion
            exclusive={false}
            panels={sections}
            defaultActiveIndex={[...Array(sections.length).keys()]}
            styled
            fluid
          />
        </>
      )}
    </FinalModalForm>
  );
}
