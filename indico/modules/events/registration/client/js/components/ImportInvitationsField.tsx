// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import inviteImportUploadURL from 'indico-url:event_registration.api_invitations_import_upload';

import type {AxiosError} from 'axios';
import React, {useCallback, useMemo} from 'react';
import {Field} from 'react-final-form';
import {Icon, Message} from 'semantic-ui-react';

import {FinalSingleFileDrop} from 'indico/react/components';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

interface ImportedInvitation {
  first_name: string;
  last_name: string;
  affiliation: string;
  email: string;
}

interface UploadErrorMessages {
  file?: string[];
}

interface UploadErrorResponse {
  messages?: UploadErrorMessages;
  webargs_errors?: UploadErrorMessages;
}

function ImportedInvitesMessage({name}: {name: string}) {
  return (
    <Field name={name} subscription={{value: true}}>
      {({input: {value}}) =>
        !!value?.length && (
          <Message info icon>
            <Icon name="info circle" />
            <PluralTranslate count={value.length} as={Message.Content}>
              <Singular>
                You are about to send <Param name="numInvitations" value={value.length} />{' '}
                invitation.
              </Singular>
              <Plural>
                You are about to send <Param name="numInvitations" value={value.length} />{' '}
                invitations.
              </Plural>
            </PluralTranslate>
          </Message>
        )
      }
    </Field>
  );
}

function getErrorMessages(error: unknown): string[] {
  const axiosError = error as AxiosError<UploadErrorResponse>;
  if (axiosError?.response?.status === 422) {
    const responseData: UploadErrorResponse = axiosError.response.data || {};
    const messages: UploadErrorMessages =
      responseData.messages || responseData.webargs_errors || {};
    const fileErrors = messages.file;
    if (fileErrors?.length) {
      return fileErrors;
    }
  }
  return [handleAxiosError(error)];
}

export default function ImportInvitationsField({
  name,
  eventId,
  regformId,
}: {
  name: string;
  eventId: number;
  regformId: number;
}) {
  const uploadURL = useMemo(
    () => inviteImportUploadURL({event_id: eventId, reg_form_id: regformId}),
    [eventId, regformId]
  );

  const onDropAccepted = useCallback(
    async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      try {
        const {data} = await indicoAxios.post<ImportedInvitation[]>(uploadURL, formData);
        return {value: data ?? [], errors: []};
      } catch (error: unknown) {
        return {value: [], errors: getErrorMessages(error)};
      }
    },
    [uploadURL]
  );

  const onDropRejected = useCallback(
    () => ({
      value: [],
      errors: [Translate.string('Please upload a valid CSV file.')],
    }),
    []
  );

  return (
    <>
      <FinalSingleFileDrop
        name={name}
        label={Translate.string('CSV file')}
        onDropAccepted={onDropAccepted}
        onDropRejected={onDropRejected}
        dropzoneOptions={{accept: ['.csv']}}
        required
      />
      <ImportedInvitesMessage name={name} />
    </>
  );
}
