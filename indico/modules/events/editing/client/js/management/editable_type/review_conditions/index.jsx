// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';

import React from 'react';
import {useParams} from 'react-router-dom';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';

import EditableTypeSubPageNav from '../EditableTypeSubPageNav';

import ReviewConditionsContext from './context';
import ReviewConditionsManager from './ReviewConditionsManager';

export default function ReviewConditionManagement() {
  const eventId = useNumericParam('event_id');
  const {type} = useParams();

  const {data: fileTypes} = useIndicoAxios(fileTypesURL({event_id: eventId, type}), {
    camelize: true,
  });

  return (
    <>
      <EditableTypeSubPageNav title={Translate.string('Review conditions')} />
      {fileTypes !== null && (
        <ReviewConditionsContext.Provider value={{eventId, editableType: type, fileTypes}}>
          <ReviewConditionsManager />
        </ReviewConditionsContext.Provider>
      )}
    </>
  );
}
