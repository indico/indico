// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createContribFormMetadataURL from 'indico-url:contributions.api_contrib_create_form_metadata';
import editContribFormMetadataURL from 'indico-url:contributions.api_contrib_edit_form_metadata';
import contributionCreateURL from 'indico-url:contributions.api_create_contrib';
import contributionURL from 'indico-url:contributions.api_manage_contrib';

import {FormApi} from 'final-form';
import _ from 'lodash';
import moment from 'moment';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {Dimmer, Form, Loader, Popup} from 'semantic-ui-react';

import {ContributionType} from 'indico/modules/events/timetable/types';
import {
  CollapsibleContainer,
  FinalContributionPersonLinkField,
  FinalLocationField,
  FinalReferences,
  FinalTagList,
} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDropdown, FinalDuration} from 'indico/react/forms/fields';
import {
  ErrorMarker,
  FinalModalForm,
  getChangedValues,
  handleSubmitError,
} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

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
  allowedKeywords: string[];
  locationParent?: Record<string, any>;
  limitFields: string[] | null;
  customFields: CustomField[];
  ignoreRequiredCustomFields: boolean;
  contributionTypes: ContributionType[];
  onSubmit: (formData: any, form?: any) => void;
  initialValues: Record<string, any>;
  sessionBlock?: Record<string, any>;
  loading: boolean;
  editing?: boolean;
  [key: string]: any; // Allow additional props
}

interface ContributionFormFieldsProps {
  eventId: number;
  locationParent?: Record<string, any>;
  personLinkFieldParams?: Record<string, any>;
  initialValues: Record<string, any>;
  limitFields?: string[] | null;
  customFields?: CustomField[];
  ignoreRequiredCustomFields?: boolean;
  contributionTypes?: ContributionType[];
  extraOptions?: Record<string, any>;
  allowedKeywords: string[];
  [key: string]: any; // Allow additional props
}

export function ContributionFormFields({
  eventId,
  locationParent = {inheriting: false},
  personLinkFieldParams = {},
  initialValues = {},
  limitFields = null,
  customFields = [],
  ignoreRequiredCustomFields = true,
  contributionTypes = [],
  extraOptions = {},
  allowedKeywords = [],
}: ContributionFormFieldsProps) {
  const showField = (name: string) => limitFields === null || limitFields.includes(name);
  const customFieldNames = customFields.map(f => `custom_fields.custom_${f.id}`);
  const customFieldsSection = customFields.map(
    ({id, fieldType, title, description, isRequired, fieldData}) => {
      // TODO: add client-side validation for max length, choices, etc at some point
      if (ignoreRequiredCustomFields) {
        isRequired = false;
      }
      const key = `custom_field_${id}`;
      const name = `custom_fields.custom_${id}`;
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

        // TODO: take alternative display settings into account (vertical/horizontal radio buttons)
        return (
          <FinalDropdown
            key={key}
            name={name}
            label={title}
            description={description}
            required={isRequired}
            options={options}
            selection
            allowNull
            nullIfEmpty
          />
        );
      } else if (fieldType === 'multiselect') {
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
            multiple
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
      {showField('title') && (
        <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      )}
      {showField('description') && (
        <FinalTextArea name="description" label={Translate.string('Description')} />
      )}
      {showField('type_id') && contributionTypes.length > 0 && (
        <FinalDropdown
          name="type_id"
          placeholder={Translate.string('No type selected')}
          label={Translate.string('Type')}
          options={contributionTypes.map(contributionType => ({
            key: contributionType.id,
            text: contributionType.name,
            description: contributionType.description,
            value: contributionType.id,
          }))}
          selection
          nullIfEmpty
        />
      )}
      {showField('start_dt') &&
        showField('duration') &&
        (initialValues.start_dt ? (
          <>
            <Field name="duration" subscription={{value: true}}>
              {({input: {value: duration}}) => (
                <FinalDateTimePicker
                  name="start_dt"
                  label={Translate.string('Start date')}
                  minStartDt={minStartDt}
                  maxEndDt={maxEndDt ? maxEndDt.clone().subtract(duration, 'seconds') : null}
                  required
                />
              )}
            </Field>
            <Field name="start_dt" subscription={{value: true}}>
              {({input: {value: startDt}}) => (
                <FinalDuration
                  name="duration"
                  label={Translate.string('Duration')}
                  max={maxEndDt ? moment(maxEndDt).diff(startDt, 'seconds') : null}
                />
              )}
            </Field>
          </>
        ) : (
          <FinalDuration name="duration" label={Translate.string('Duration')} />
        ))}
      {showField('person_links') && (
        <FinalContributionPersonLinkField
          name="person_links"
          label={Translate.string('People')}
          eventId={eventId}
          sessionUser={{...Indico.User, userId: Indico.User.id}}
          {...personLinkFieldParams}
        />
      )}
      {showField('location_data') && (
        <FinalLocationField
          name="location_data"
          label={Translate.string('Location')}
          locationParent={locationParent}
        />
      )}
      {showField('keywords') &&
        (allowedKeywords.length ? (
          <FinalDropdown
            name="keywords"
            label={Translate.string('Keywords')}
            multiple
            selection
            options={[...new Set([...allowedKeywords, ...initialValues.keywords])].map(keyword => ({
              value: keyword,
              text: keyword,
              key: keyword,
            }))}
            placeholder={Translate.string('Please choose a keyword')}
          />
        ) : (
          <FinalTagList
            name="keywords"
            label={Translate.string('Keywords')}
            placeholder={Translate.string('Please enter a keyword')}
          />
        ))}
      {(showField('custom_fields') ||
        showField('references') ||
        showField('board_number') ||
        showField('code')) && (
        <CollapsibleContainer
          title={
            <span style={{display: 'inline-flex', alignItems: 'center', gap: '0.5rem'}}>
              <Translate>Advanced</Translate>
              <Popup
                trigger={<ErrorMarker fields={[...customFieldNames, 'references']} size="tiny" />}
              >
                <Translate>Please expand this section and correct the invalid fields.</Translate>
              </Popup>
            </span>
          }
          dividing
        >
          {showField('custom_fields') && customFieldsSection}
          {showField('references') && (
            <FinalReferences
              name="references"
              label={Translate.string('External IDs')}
              description={Translate.string('Manage external resources for this contribution')}
            />
          )}
          {(showField('board_number') || showField('code')) && (
            <Form.Group widths="equal">
              {showField('board_number') && (
                <FinalInput name="board_number" label={Translate.string('Board number')} />
              )}
              {showField('code') && (
                <FinalInput name="code" label={Translate.string('Program code')} />
              )}
            </Form.Group>
          )}
        </CollapsibleContainer>
      )}
    </>
  );
}

function ContributionForm({
  eventId,
  personLinkFieldParams = {},
  locationParent = {},
  limitFields = null,
  customFields = [],
  ignoreRequiredCustomFields = false,
  contributionTypes = [],
  onSubmit,
  initialValues = {},
  allowedKeywords = [],
  sessionBlock = null,
  loading,
  editing = false,
  ...rest
}: ContributionFormProps) {
  const handleSubmit = async (formData: any, form: FormApi) => {
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
      person_links: personLinks,
    };
    const submitPayload = editing ? getChangedValues(formData, form) : formData;
    return await onSubmit(submitPayload);
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
      style={{overflowWrap: 'break-word'}}
      onSubmit={handleSubmit}
      initialValues={initialValues}
      size="small"
      {...rest}
    >
      <ContributionFormFields
        eventId={eventId}
        locationParent={locationParent}
        initialValues={initialValues}
        sessionBlock={sessionBlock}
        limitFields={limitFields}
        customFields={customFields}
        ignoreRequiredCustomFields={ignoreRequiredCustomFields}
        contributionTypes={contributionTypes}
        personLinkFieldParams={personLinkFieldParams}
        allowedKeywords={allowedKeywords}
      />
    </FinalModalForm>
  );
}

export function ContributionEditForm({
  eventId,
  contribId,
  onSubmit,
  onClose,
}: {
  eventId: number;
  contribId: number;
  onSubmit?: (formData: any, form: any) => void;
  onClose: () => void;
}) {
  const {data: metadata, loading: metadataLoading} = useIndicoAxios(
    editContribFormMetadataURL({event_id: eventId, contrib_id: contribId})
  );
  const contribURL = contributionURL(snakifyKeys({eventId, contribId}));
  const {data: contrib, loading: contribLoading} = useIndicoAxios(contribURL);

  const handleSubmit = async (formData: any) => {
    try {
      await indicoAxios.patch(contribURL, formData);
    } catch (e) {
      return handleSubmitError(e, {}, ['custom_fields']);
    }

    location.reload();
    // never finish submitting to avoid fields being re-enabled
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    await new Promise(() => {});
  };

  const loading = contribLoading || metadataLoading;

  const {
    locationParent,
    allowedKeywords,
    personLinkFieldParams,
    limitFields,
    ignoreRequiredCustomFields,
    customFields: fields,
    types: contributionTypes,
  } = camelizeKeys(metadata ?? {});

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      allowedKeywords={allowedKeywords}
      locationParent={locationParent}
      limitFields={limitFields}
      customFields={fields}
      ignoreRequiredCustomFields={ignoreRequiredCustomFields}
      contributionTypes={contributionTypes}
      header={Translate.string("Edit contribution '{title}'", {title: contrib?.title})}
      onSubmit={onSubmit ?? handleSubmit}
      onClose={onClose}
      initialValues={
        loading
          ? {}
          : {
              ..._.omit(contrib, 'session_block'),
              person_links: camelizeKeys(contrib.person_links),
            }
      }
      sessionBlock={camelizeKeys(contrib?.session_block)}
      loading={loading}
      editing
    />
  );
}

export function ContributionCreateForm({
  eventId,
  onClose,
  onCreate,
}: {
  eventId: number;
  onClose: () => void;
  onCreate?: (contrib: any) => void;
}) {
  const {data: metadata, loading} = useIndicoAxios(
    createContribFormMetadataURL({event_id: eventId})
  );

  const {
    locationParent,
    defaultDuration,
    allowedKeywords,
    personLinkFieldParams,
    limitFields,
    ignoreRequiredCustomFields,
    customFields: fields,
    types: contributionTypes,
  } = camelizeKeys(metadata ?? {});

  const handleSubmit = async (formData: any) => {
    try {
      const response = await indicoAxios.post(contributionCreateURL({event_id: eventId}), formData);
      if (onCreate) {
        onCreate(response.data);
      } else {
        location.reload();
        // never finish submitting to avoid fields being re-enabled
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        await new Promise(() => {});
      }
    } catch (e) {
      return handleSubmitError(e, {}, ['custom_fields']);
    }

    onClose();
  };

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};

  const defaultValuesByType = {
    text: '',
    single_choice: null,
    multiselect: [],
  };

  const initialValues = loading
    ? {}
    : {
        duration: defaultDuration,
        person_links: [],
        keywords: [],
        references: [],
        location_data: locationData,
        custom_fields: Object.fromEntries(
          fields.map((field: any) => [`custom_${field.id}`, defaultValuesByType[field.fieldType]])
        ),
      };

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      allowedKeywords={allowedKeywords}
      locationParent={locationParent}
      limitFields={limitFields}
      customFields={fields ?? []}
      ignoreRequiredCustomFields={ignoreRequiredCustomFields}
      contributionTypes={contributionTypes}
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
  className,
}: {
  eventId: number;
  contribId: number;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <a
        className={className}
        title={Translate.string('Edit contribution (new React-based dialog)')}
        onClick={evt => {
          evt.preventDefault();
          evt.stopPropagation();
          setOpen(true);
        }}
      />
      {open && (
        <ContributionEditForm
          eventId={eventId}
          contribId={contribId}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

export function CreateContributionButton({eventId}: {eventId: number}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button type="button" className="i-button highlight icon-plus" onClick={() => setOpen(true)}>
        <Translate>New contribution (React)</Translate>
      </button>
      {open && <ContributionCreateForm eventId={eventId} onClose={() => setOpen(false)} />}
    </>
  );
}
