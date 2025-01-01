// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import manageTagsURL from 'indico-url:event_editing.manage_tags';

import React from 'react';
import {Link} from 'react-router-dom';

import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';

import EditableTypeList from './EditableTypeList';
import ManageService from './ManageService';
import Section from './Section';

export default function EditingManagementDashboard() {
  const eventId = useNumericParam('event_id');
  return (
    <>
      <div className="action-box">
        <Section
          icon="tag"
          label={Translate.string('Tags')}
          description={Translate.string('Configure the tags that can be assigned to revisions')}
        >
          <Link to={manageTagsURL({event_id: eventId})} className="i-button icon-settings">
            <Translate>Configure</Translate>
          </Link>
        </Section>
        {Indico.ExperimentalEditingService && <ManageService eventId={eventId} />}
      </div>
      <EditableTypeList eventId={eventId} />
    </>
  );
}
