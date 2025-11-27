// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import type {FormApi} from 'final-form';
import React, {useCallback, useMemo, useState} from 'react';
import {Accordion, Form, Loader} from 'semantic-ui-react';

import {FinalInput, getChangedValues, handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';
import {getPluginObjects} from 'indico/utils/plugins';

import {FinalStringListField} from './StringListField';
import {AffiliationFormValues} from './types';

const defaultValues: AffiliationFormValues = {
  name: '',
  altNames: [],
  street: '',
  postcode: '',
  city: '',
  countryCode: '',
};

export default function AffiliationFormDialog({
  trigger,
  affiliationURL,
  onSuccess,
  edit = false,
}: {
  trigger: React.ReactElement;
  affiliationURL: string;
  onSuccess: (data: AffiliationFormValues) => void;
  edit?: boolean;
}) {
  const [open, setOpen] = useState<boolean>(false);
  const {data: initialValues, loading} = useIndicoAxios(affiliationURL, {
    manual: !open || !edit,
    camelize: true,
  });

  const handleTriggerClick = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      if (trigger.props.onClick) {
        trigger.props.onClick(event);
      }
      if (event.defaultPrevented || trigger.props.disabled) {
        return;
      }
      setOpen(true);
    },
    [trigger]
  );
  const triggerWithHandler = useMemo(
    () => React.cloneElement(trigger, {onClick: handleTriggerClick}),
    [trigger, handleTriggerClick]
  );

  const handleSubmit = useCallback(
    async (formData: AffiliationFormValues, form: FormApi<AffiliationFormValues>) => {
      try {
        const payload = snakifyKeys(edit ? getChangedValues(formData, form) : formData);
        const submitMethod = edit ? indicoAxios.patch : indicoAxios.post;
        const response = await submitMethod(affiliationURL, payload);
        onSuccess(camelizeKeys(response.data));
        setOpen(false);
      } catch (error) {
        return handleSubmitError(error);
      }
    },
    [affiliationURL, edit, onSuccess]
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
              <FinalInput
                name="countryCode"
                label={Translate.string('Country code')}
                description={Translate.string('Enter an ISO-3166 two letter country code.')}
              />
            </Form.Group>
          </>
        ),
      },
    },
    ...getPluginObjects('affiliation-form-sections').flat(),
  ];

  return (
    <>
      {triggerWithHandler}
      {open && (
        <FinalModalForm
          id="affiliation-form-modal"
          size="small"
          header={edit ? Translate.string('Edit affiliation') : Translate.string('Add affiliation')}
          onClose={() => setOpen(false)}
          onSubmit={handleSubmit}
          submitLabel={Translate.string('Save')}
          initialValues={{...defaultValues, ...initialValues}}
          disabledUntilChange
        >
          {edit && (loading || !initialValues) ? (
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
                panels={formSections}
                defaultActiveIndex={[...Array(formSections.length).keys()]}
                styled
                fluid
              />
            </>
          )}
        </FinalModalForm>
      )}
    </>
  );
}
