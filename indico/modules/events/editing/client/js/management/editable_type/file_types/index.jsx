// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createFileTypeURL from 'indico-url:event_editing.api_add_file_type';
import editFileTypeURL from 'indico-url:event_editing.api_edit_file_type';
import fileTypeURL from 'indico-url:event_editing.api_file_types';

import React from 'react';
import {useParams} from 'react-router-dom';

import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';

import EditableTypeSubPageNav from '../EditableTypeSubPageNav';

import FileTypeManager from './FileTypeManager';

export default function FileTypeManagement() {
  const eventId = useNumericParam('event_id');
  const {type} = useParams();

  return (
    <>
      <EditableTypeSubPageNav title={Translate.string('File types')} />
      <FileTypeManager
        eventId={eventId}
        getAllURLFn={params => fileTypeURL({type, ...params})}
        editURLFn={params => editFileTypeURL({type, ...params})}
        createURLFn={params => createFileTypeURL({type, ...params})}
      />
    </>
  );
}
