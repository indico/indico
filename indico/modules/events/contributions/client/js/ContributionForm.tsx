// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contribFieldsURL from 'indico-url:contributions.api_contrib_fields';
import locationParentContribURL from 'indico-url:contributions.api_contrib_location_parent';
import contribPersonLinkFieldParamsURL from 'indico-url:contributions.api_contrib_person_link_params';
import defaultDurationURL from 'indico-url:contributions.api_contribs_duration';
import locationParentURL from 'indico-url:contributions.api_contribs_location_parent';
import contributionCreateURL from 'indico-url:contributions.api_create_contrib';
import contributionURL from 'indico-url:contributions.api_manage_contrib';
import personLinkFieldParamsURL from 'indico-url:events.api_person_link_params';

import _ from 'lodash';
import React, {useEffect, useState} from 'react';
import {Field} from 'react-final-form';
import {Button, Dimmer, Form, Loader} from 'semantic-ui-react';

import {
  CollapsibleContainer,
  FinalLocationField,
  FinalReferences,
  FinalTagList,
} from 'indico/react/components';
import {FinalContributionPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDropdown, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';
import {toMoment} from 'indico/utils/date';

interface CustomField {
  id: number;
  fieldType: string;
  title: string;
  description: string;
  isRequired: boolean;
  fieldData: {
    multiline?: boolean;
    options?: {id: string; option: string}[];
  };
}

interface ContributionFormProps {
  eventId: number;
  personLinkFieldParams?: Record<string, any>;
  locationParent?: Record<string, any>;
  customFields: CustomField[];
  onSubmit: (formData: any) => void;
  initialValues: Record<string, any>;
  sessionBlock?: Record<string, any>;
  loading: boolean;
  [key: string]: any; // Allow additional props
}

interface ContributionFormFieldsProps {
  eventId: number;
  locationParent?: Record<string, any>;
  personLinkFieldParams?: Record<string, any>;
  initialValues: Record<string, any>;
  sessionBlock?: Record<string, any>;
  customFields?: CustomField[];
  extraOptions?: Record<string, any>;
  [key: string]: any; // Allow additional props
}

export function ContributionFormFields({
  eventId,
  locationParent = {inheriting: false},
  personLinkFieldParams = {},
  initialValues = {},
  sessionBlock = null,
  customFields = [],
  extraOptions = {},
}: ContributionFormFieldsProps) {
  const customFieldsSection = customFields.map(
    ({id, fieldType, title, description, isRequired, fieldData}) => {
      const key = `custom_field_${id}`;
      const name = `custom_fields.field_${id}`;
      if (fieldType === 'text') {
        if (fieldData.multiline) {
          return (
            <FinalTextArea
              key={key}
              name={name}
              label={title}
              description={description}
              required={isRequired}
            />
          );
        } else {
          return (
            <FinalInput
              key={key}
              name={name}
              label={title}
              description={description}
              required={isRequired}
            />
          );
        }
      } else if (fieldType === 'single_choice') {
        const options = fieldData.options!.map(opt => ({
          key: opt.id,
          text: opt.option,
          value: opt.id,
        }));

        return (
          <FinalDropdown
            key={key}
            name={name}
            label={title}
            description={description}
            required={isRequired}
            options={options}
            selection
          />
        );
      } else {
        console.warn('Unsupported field type', fieldType);
        return null;
      }
    }
  );

  const {minStartDt, maxEndDt} = extraOptions;
  return (
    <>
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      {initialValues.start_dt ? (
        <>
          <Field name="duration" subscription={{value: true}}>
            {({input: {value: duration}}) => (
              <FinalDateTimePicker
                name="start_dt"
                label={Translate.string('Start date')}
                sessionBlock={sessionBlock}
                minStartDt={minStartDt || (sessionBlock && toMoment(sessionBlock.startDt))}
                maxEndDt={
                  maxEndDt ||
                  (sessionBlock && toMoment(sessionBlock.endDt).subtract(duration, 'second'))
                }
                required
              />
            )}
          </Field>
          <Field name="start_dt" subscription={{value: true}}>
            {({input: {value: startDt}}) => (
              <FinalDuration
                name="duration"
                label={Translate.string('Duration')}
                max={
                  sessionBlock && toMoment(sessionBlock.endDt).diff(toMoment(startDt), 'seconds')
                }
              />
            )}
          </Field>
        </>
      ) : (
        <FinalDuration name="duration" label={Translate.string('Duration')} />
      )}
      <FinalContributionPersonLinkField
        name="person_links"
        label={Translate.string('People')}
        eventId={eventId}
        sessionUser={{...Indico.User, userId: Indico.User.id}}
        {...personLinkFieldParams}
      />
      <FinalLocationField
        name="location_data"
        label={Translate.string('Location')}
        locationParent={locationParent}
      />
      <FinalTagList
        name="keywords"
        label={Translate.string('Keywords')}
        placeholder={Translate.string('Please enter a keyword')}
      />
      {customFieldsSection}
      <CollapsibleContainer title={Translate.string('Advanced')} dividing>
        <FinalReferences
          name="references"
          label={Translate.string('External IDs')}
          description={Translate.string('Manage external resources for this contribution')}
        />
        <Form.Group widths="equal">
          <FinalInput name="board_number" label={Translate.string('Board number')} />
          <FinalInput name="code" label={Translate.string('Program code')} />
        </Form.Group>
      </CollapsibleContainer>
    </>
  );
}

export function ContributionForm({
  eventId,
  personLinkFieldParams = {},
  locationParent = {},
  customFields = [],
  onSubmit,
  initialValues = {},
  sessionBlock = null,
  loading,
  ...rest
}: ContributionFormProps) {
  const handleSubmit = (formData: any) => {
    const customFieldsData = Object.entries(formData.custom_fields).map(([key, data]) => ({
      id: parseInt(key.replace('field_', ''), 10),
      data,
    }));
    const personLinks = formData.person_links.map(
      ({
        affiliationMeta,
        avatarURL,
        favoriteUsers,
        fullName,
        id,
        isAdmin,
        language,
        name,
        userId,
        userIdentifier,
        invalid,
        detail,
        ...personLinkData
      }) =>
        snakifyKeys({
          ...personLinkData,
        })
    );
    formData = {
      ...formData,
      custom_fields: customFieldsData,
      person_links: personLinks,
    };
    onSubmit({
      ...formData,
      references: formData.references.map(({id, ...refs}: any) => refs),
    });
  };

  if (loading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  return (
    <FinalModalForm
      id="contribution-form"
      onSubmit={handleSubmit}
      initialValues={initialValues}
      size="small"
      {...rest}
    >
      <ContributionFormFields
        {...{locationParent, initialValues, sessionBlock, customFields, personLinkFieldParams}}
      />
    </FinalModalForm>
  );
}

export function ContributionEditForm({
  eventId,
  contribId,
  onClose,
}: {
  eventId: number;
  contribId: number;
  onClose: () => void;
}) {
  const {data: personLinkFieldParams, loading: personLinkFieldParamsLoading} = useIndicoAxios(
    contribPersonLinkFieldParamsURL({event_id: eventId, contrib_id: contribId}),
    {camelize: true}
  );
  const {data: fields, loading: fieldsLoading} = useIndicoAxios(
    contribFieldsURL({event_id: eventId}),
    {camelize: true}
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentContribURL({event_id: eventId, contrib_id: contribId})
  );
  const contribURL = contributionURL(snakifyKeys({eventId, contribId}));
  const {data: contrib, loading: contribLoading} = useIndicoAxios(contribURL);

  const handleSubmit = async (formData: any) => {
    try {
      await indicoAxios.patch(contribURL, formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const loading =
    contribLoading || locationParentLoading || fieldsLoading || personLinkFieldParamsLoading;

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      locationParent={locationParent}
      customFields={fields}
      header={Translate.string("Edit contribution '{title}'", {title: contrib?.title})}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={
        loading
          ? {}
          : {
              ..._.omit(contrib, 'session_block'),
              custom_fields: Object.fromEntries(
                contrib.custom_fields.map((field: any) => [`field_${field.id}`, field.data])
              ),
              person_links: camelizeKeys(contrib.person_links),
            }
      }
      sessionBlock={camelizeKeys(contrib?.session_block)}
      loading={loading}
    />
  );
}

export function ContributionCreateForm({
  eventId,
  onClose,
  customFields = {},
  customInitialValues = {},
}: {
  eventId: number;
  onClose: () => void;
  customFields?: Record<string, any>;
  customInitialValues?: Record<string, any>;
}) {
  const {data: personLinkFieldParams, loading: personLinkFieldParamsLoading} = useIndicoAxios(
    personLinkFieldParamsURL({event_id: eventId}),
    {camelize: true}
  );
  const {data: fields, loading: fieldsLoading} = useIndicoAxios(
    contribFieldsURL({event_id: eventId}),
    {camelize: true}
  );
  const {data: defaultDuration, loading: defaultDurationLoading} = useIndicoAxios(
    defaultDurationURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );

  const handleSubmit = async (formData: any) => {
    try {
      await indicoAxios.post(contributionCreateURL({event_id: eventId}), formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};
  const loading =
    locationParentLoading ||
    defaultDurationLoading ||
    fieldsLoading ||
    personLinkFieldParamsLoading;

  const initialValues = loading
    ? {}
    : {
        duration: defaultDuration,
        person_links: [],
        keywords: [],
        references: [],
        location_data: locationData,
        custom_fields: {
          ...Object.fromEntries(fields.map((field: any) => [`field_${field.id}`, ''])),
          ...customFields,
        },
        ...customInitialValues,
      };

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      locationParent={locationParent}
      customFields={(fields ?? []).concat(Object.values(customFields))}
      header={Translate.string('Add new contribution')}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={initialValues}
      loading={loading}
    />
  );
}

export function EditContributionButton({
  eventId,
  contribId,
  eventTitle,
  triggerSelector,
  ...rest
}: {
  eventId: number;
  contribId: number;
  eventTitle: string;
  triggerSelector?: string;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Button onClick={() => setOpen(true)} {...rest}>
          <Translate>Edit contribution</Translate>
        </Button>
      )}
      {open && (
        <ContributionEditForm
          eventId={eventId}
          contribId={contribId}
          eventTitle={eventTitle}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

export function CreateContributionButton({
  eventId,
  triggerSelector,
  ...rest
}: {
  eventId: number;
  triggerSelector?: string;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Button onClick={() => setOpen(true)} {...rest}>
          <Translate>Edit contribution</Translate>
        </Button>
      )}
      {open && (
        <ContributionCreateForm
          eventId={eventId}
          onClose={() => setOpen(false)}
          customFields={{}}
          customInitialValues={{}}
        />
      )}
    </>
  );
}
