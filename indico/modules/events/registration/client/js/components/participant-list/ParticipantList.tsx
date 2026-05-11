// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import participantListDataURL from 'indico-url:event_registration.api_participant_list';
import participantListPreviewURL from 'indico-url:event_registration.manage_participant_list_preview';

import React, {ReactNode, useMemo} from 'react';
import {
  Button,
  Icon,
  MenuItem,
  Message,
  MessageContent,
  Tab,
  Popup,
  TabPane,
  Loader,
} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

import {ParticipantCountHidden} from './ParticipantSharedTranslations';
import ParticipantTable from './ParticipantTable';
import {PreviewEnum, TableObj} from './types';

import './ParticipantList.module.scss';

interface ParticipantListProps {
  eventId: number;
  preview?: PreviewEnum;
}

interface ParticipantCounterProps {
  table: TableObj;
}

function ParticipantCounter({table}: ParticipantCounterProps) {
  return (
    <Popup
      position="left center"
      content={
        <ParticipantCountHidden
          count={table.num_participants}
          countHidden={table.num_anonymous_participants}
        />
      }
      trigger={
        <div styleName="participants-count-wrapper">
          {table.num_anonymous_participants > 0 && (
            <>
              <span styleName="hidden">{table.num_anonymous_participants}</span>/
            </>
          )}
          {table.num_participants}
          <Icon name="user" />
        </div>
      }
    />
  );
}

export default function ParticipantList({eventId, preview}: ParticipantListProps) {
  const url = useMemo(
    () =>
      participantListDataURL({
        event_id: eventId,
        ...(preview ? {preview} : {}),
      }),
    [eventId, preview]
  );

  const {data, loading, lastData} = useIndicoAxios(url);

  let viewToggle: ReactNode, infoContent: ReactNode;

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

  if ((loading || !data) && !lastData) {
    return <Loader active inline="centered" />;
  }

  if (!data?.published) {
    infoContent = <Translate>There are no published registrations.</Translate>;
  } else if (data.num_participants === 0) {
    infoContent = <Translate>There are no registrations yet.</Translate>;
  }

  if (infoContent) {
    return (
      <Message info size="large">
        <MessageContent>
          <Icon name="info circle" />
          {infoContent}
        </MessageContent>
      </Message>
    );
  }

  return (
    <section>
      {viewToggle}
      {data.merged ? (
        <ParticipantTable table={data.tables[0]} />
      ) : (
        <Tab
          styleName="tab-menu"
          menu={{secondary: true}}
          panes={data.tables.map((table: TableObj) => ({
            menuItem: (
              <MenuItem styleName="tab-title" key={table.title}>
                {table.title}
                <ParticipantCounter table={table} />
              </MenuItem>
            ),
            render: () => (
              <TabPane key={table.title} attached={false}>
                <ParticipantTable table={table} />
              </TabPane>
            ),
          }))}
        />
      )}
    </section>
  );
}
