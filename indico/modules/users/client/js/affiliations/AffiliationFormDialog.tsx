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

import {FinalDropdown, FinalInput, getChangedValues, handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';
import {getPluginObjects} from 'indico/utils/plugins';

import FinalStringListField from './StringListField';
import {AffiliationFormValues} from './types';

const isoToFlag = (country: string) =>
  String.fromCodePoint(...country.split('').map(char => char.charCodeAt(0) + 0x1f1a5));

const defaultValues: AffiliationFormValues = {
  name: '',
  altNames: [],
  street: '',
  postcode: '',
  city: '',
  countryCode: '',
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
      const payload = snakifyKeys(edit ? getChangedValues(formData, form) : formData);
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
                name="countryCode"
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
        name="altNames"
        label={Translate.string('Alternative names')}
        placeholder={Translate.string('Type a name and press Enter to add')}
      />
      <Accordion
        exclusive={false}
        panels={formSections}
        defaultActiveIndex={[...Array(formSections.length).keys()]}
        styled
        fluid
      />
    </FinalModalForm>
  );
}
