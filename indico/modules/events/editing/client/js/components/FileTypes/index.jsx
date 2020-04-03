// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useParams} from 'react-router-dom';
import {useNumericParam} from 'indico/react/util/routing';
import {Translate} from 'indico/react/i18n';
import EditingTypeSubPageNav from '../EditingTypeSubPageNav';
import FileTypeManager from './FileTypeManager';

export default function FileTypeManagement() {
  const eventId = useNumericParam('confId');
  const {type} = useParams();

  return (
    <>
      <EditingTypeSubPageNav title={Translate.string('File types')} />
      <FileTypeManager eventId={eventId} editableType={type} />
    </>
  );
}
