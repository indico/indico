// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import participantListPreviewURL from 'indico-url:event_registration.manage_participant_list_preview';

import React from 'react';
import {Button, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import ParticipantAccordion from './ParticipantAccordion';
import {PreviewEnum, TableObj} from './types';

import './ParticipantList.module.scss';

interface ParticipantListProps {
  published: boolean;
  merged: boolean;
  totalParticipantCount: number;
  tables: TableObj[];
  eventId: number;
  preview?: PreviewEnum;
}

export default function ParticipantList({
  published,
  totalParticipantCount,
  tables,
  preview,
  eventId,
  merged,
}: ParticipantListProps) {
  let viewToggle;

  if (preview === PreviewEnum.GUEST) {
    viewToggle = (
      <Button
        basic
        color="blue"
        href={participantListPreviewURL({event_id: eventId})}
        styleName="view-toggle"
      >
        <Icon name="user" />
        <Translate>Show registered participant view instead</Translate>
      </Button>
    );
  } else if (preview) {
    viewToggle = (
      <Button
        basic
        color="blue"
        href={participantListPreviewURL({event_id: eventId, guest: 1})}
        styleName="view-toggle"
      >
        <Icon name="user secret" />
        <Translate>Show unregistered guest view instead</Translate>
      </Button>
    );
  }

  return (
    <section>
      {viewToggle}
      <ParticipantAccordion
        published={published}
        totalParticipantCount={totalParticipantCount}
        tables={tables}
        merged={merged}
      />
    </section>
  );
}
