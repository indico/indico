// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import countriesURL from 'indico-url:users.api_countries';

import type {FormApi} from 'final-form';
import React, {useCallback} from 'react';
import {Accordion, Form} from 'semantic-ui-react';

import {
  FinalDropdown,
  FinalInput,
  FinalTextArea,
  getChangedValues,
  handleSubmitError,
} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {getPluginObjects} from 'indico/utils/plugins';

import FinalStringListField from './StringListField';
import {AffiliationFormValues} from './types';

const isoToFlag = (country: string) =>
  String.fromCodePoint(...country.split('').map(char => char.charCodeAt(0) + 0x1f1a5));

const defaultValues: AffiliationFormValues = {
  name: '',
  alt_names: [],
  street: '',
  postcode: '',
  city: '',
  country_code: '',
  meta: {},
};

const formatMetaValue = (value: unknown) =>
  typeof value === 'string' ? value : JSON.stringify(value, null, 2);

const parseMetaValue = (value: string) => {
  if (!value) {
    return {};
  }
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
};

const validateMetaValue = (value: unknown) => {
  if (!value || Array.isArray(value)) {
    return Translate.string('Enter a JSON object');
  }
  if (typeof value === 'string') {
    try {
      JSON.parse(value);
    } catch (error) {
      return error.message;
    }
  }
};

export default function AffiliationFormDialog({
  affiliationURL,
  open,
  onClose,
  initialValues,
  onSuccess,
  edit = false,
}: {
  affiliationURL: string;
  open: boolean;
  onClose: () => void;
  initialValues?: AffiliationFormValues;
  onSuccess: () => void;
  edit?: boolean;
}) {
  const {data: countries} = useIndicoAxios(countriesURL({}), {manual: !open});

  const handleSubmit = useCallback(
    async (formData: AffiliationFormValues, form: FormApi<AffiliationFormValues>) => {
      const payload = edit ? getChangedValues(formData, form) : formData;
      try {
        edit
          ? await indicoAxios.patch(affiliationURL, payload)
          : await indicoAxios.post(affiliationURL, payload);
      } catch (error) {
        return handleSubmitError(error);
      }
      onSuccess();
      onClose();
    },
    [affiliationURL, edit, onClose, onSuccess]
  );

  const formSections = [
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
              <FinalDropdown
                name="country_code"
                label={Translate.string('Country')}
                fluid
                selection
                placeholder={Translate.string('Select a country')}
                options={(countries ?? []).map(([name, title]) => ({
                  key: name,
                  value: name,
                  text: `${isoToFlag(name)} ${title}`,
                }))}
                loading={!countries}
                disabled={!countries}
              />
            </Form.Group>
          </>
        ),
      },
    },
    ...getPluginObjects('affiliation-form-sections').flat(),
    {
      key: 'advanced',
      title: Translate.string('Advanced'),
      content: {
        content: (
          <FinalTextArea
            name="meta"
            label={Translate.string('Metadata (JSON)')}
            placeholder={Translate.string('Enter a JSON object')}
            className="mono"
            format={formatMetaValue}
            formatOnBlur={false}
            parse={parseMetaValue}
            validate={validateMetaValue}
            rows={4}
          />
        ),
      },
    },
  ];

  if (!open) {
    return null;
  }

  return (
    <FinalModalForm
      id="affiliation-form-modal"
      size="small"
      header={edit ? Translate.string('Edit affiliation') : Translate.string('Add affiliation')}
      onClose={onClose}
      onSubmit={handleSubmit}
      submitLabel={Translate.string('Save')}
      initialValues={{...defaultValues, ...(initialValues || {})}}
      disabledUntilChange
    >
      <FinalInput name="name" label={Translate.string('Name')} required />
      <FinalStringListField
        name="alt_names"
        label={Translate.string('Alternative names')}
        placeholder={Translate.string('Type a name and press Enter to add')}
      />
      <Accordion
        exclusive={false}
        panels={formSections}
        defaultActiveIndex={[...Array(formSections.length - 1).keys()]}
        styled
        fluid
      />
    </FinalModalForm>
  );
}
