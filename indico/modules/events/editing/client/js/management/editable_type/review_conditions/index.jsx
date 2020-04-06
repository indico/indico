// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';

import React from 'react';
import {useParams} from 'react-router-dom';
import {useNumericParam} from 'indico/react/util/routing';
import {Translate} from 'indico/react/i18n';
import {useIndicoAxios} from 'indico/react/hooks';
import EditableTypeSubPageNav from '../EditableTypeSubPageNav';
import ReviewConditionsManager from './ReviewConditionsManager';
import ReviewConditionsContext from './context';

export default function ReviewConditionManagement() {
  const eventId = useNumericParam('confId');
  const {type} = useParams();

  const {data: fileTypes} = useIndicoAxios({
    url: fileTypesURL({confId: eventId, type}),
    camelize: true,
    trigger: [eventId, type],
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
