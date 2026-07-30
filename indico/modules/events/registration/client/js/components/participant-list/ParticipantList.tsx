// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import participantListDataURL from 'indico-url:event_registration.api_participant_list';
import participantListDataPreviewURL from 'indico-url:event_registration.api_participant_list_preview';

import React, {ReactNode, useMemo, useState} from 'react';
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
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import {ParticipantCountHidden} from './ParticipantCountHidden';
import ParticipantTable, {PerPageOptions} from './ParticipantTable';
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
              <span styleName="hidden">{table.num_anonymous_participants}</span>/{' '}
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
  const [search, setSearch] = useState('');
  const [perPage, setPerPage] = useState<PerPageOptions>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [previewMode, setPreviewMode] = useState<PreviewEnum | undefined>(preview);

  const url = useMemo(() => {
    if (previewMode) {
      return participantListDataPreviewURL({
        event_id: eventId,
        guest: previewMode === PreviewEnum.GUEST ? '1' : '0',
      });
    }
    return participantListDataURL({event_id: eventId});
  }, [eventId, previewMode]);

  const {data, loading, lastData} = useIndicoAxios(url);

  const perPageOptions: PerPageOptions[] = useMemo(() => {
    const maxNumberOfParticipants = (data?.tables ?? []).reduce(
      (max, table) => Math.max(max, table.num_participants),
      0
    );

    if (maxNumberOfParticipants > 0) {
      const options = [25, 50, 100].filter(opt => opt < maxNumberOfParticipants);
      return [...options, 'all'];
    }
    return ['all'];
  }, [data]);

  let viewToggle: ReactNode, infoContent: ReactNode;

  if (previewMode === PreviewEnum.GUEST) {
    viewToggle = (
      <Button
        basic
        color="blue"
        onClick={() => setPreviewMode(PreviewEnum.PARTICIPANT)}
        styleName="view-toggle"
      >
        <Icon name="user" />
        <Translate>Show registered participant view instead</Translate>
      </Button>
    );
  } else if (previewMode) {
    viewToggle = (
      <Button
        basic
        color="blue"
        onClick={() => setPreviewMode(PreviewEnum.GUEST)}
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
      <>
        {viewToggle}
        <Message info size="large">
          <MessageContent>
            <Icon name="info circle" />
            {infoContent}
          </MessageContent>
        </Message>
      </>
    );
  }

  return (
    <section>
      {viewToggle}
      <h3 styleName="participant-total-count">
        <PluralTranslate count={data.num_participants}>
          <Singular>
            <Param name="count" value={data.num_participants} /> participant
          </Singular>
          <Plural>
            <Param name="count" value={data.num_participants} /> participants
          </Plural>
        </PluralTranslate>
      </h3>
      {data.merged ? (
        <ParticipantTable
          table={data.tables[0]}
          search={search}
          setSearch={setSearch}
          perPageOptions={perPageOptions}
          perPage={perPage}
          setPerPage={setPerPage}
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
        />
      ) : (
        <Tab
          styleName="tab-menu"
          menu={{secondary: true}}
          panes={data.tables.map((table: TableObj) => ({
            menuItem: (
              <MenuItem styleName="tab-title" key={table.title}>
                <span styleName="title-text" title={table.title}>
                  {table.title}
                </span>
                <ParticipantCounter table={table} />
              </MenuItem>
            ),
            render: () => (
              <TabPane key={table.title} attached={false}>
                <ParticipantTable
                  table={table}
                  merged={data.merged}
                  search={search}
                  setSearch={setSearch}
                  perPageOptions={perPageOptions}
                  perPage={perPage}
                  setPerPage={setPerPage}
                  currentPage={currentPage}
                  setCurrentPage={setCurrentPage}
                />
              </TabPane>
            ),
          }))}
        />
      )}
    </section>
  );
}
