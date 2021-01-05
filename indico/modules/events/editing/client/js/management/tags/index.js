// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import dashboardURL from 'indico-url:event_editing.dashboard';

import React from 'react';

import {ManagementPageBackButton, ManagementPageSubTitle} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';

import TagManager from './TagManager';

export default function EditingTagManagement() {
  const eventId = useNumericParam('confId');
  return (
    <>
      <ManagementPageBackButton url={dashboardURL({confId: eventId})} />
      <ManagementPageSubTitle title={Translate.string('Tags')} />
      <TagManager eventId={eventId} />
    </>
  );
}
