// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {ReactNode, useState} from 'react';
import {
  AccordionTitle,
  AccordionContent,
  Accordion,
  Icon,
  Popup,
  Message,
  MessageContent,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {ParticipantCountHidden} from './ParticipantSharedTranslations';
import ParticipantTable from './ParticipantTable';
import {TableObj} from './types';

import './ParticipantAccordion.module.scss';

interface ParticipantCounterProps {
  totalCount: number;
  hiddenCount: number;
}

interface ParticipantAccordionItemProps {
  table: TableObj;
  collapsible?: boolean;
  noTitle?: boolean;
}

interface ParticipantAccordionProps {
  totalParticipantCount: number;
  published: boolean;
  tables: TableObj[];
  merged?: boolean;
}

function ParticipantCounter({totalCount, hiddenCount}: ParticipantCounterProps) {
  const participantCounterElement = (
    <span styleName="participants-count-wrapper">
      {totalCount} <Icon name="user" />
    </span>
  );

  return hiddenCount > 0 ? (
    <Popup
      position="left center"
      content={<ParticipantCountHidden count={hiddenCount} />}
      trigger={participantCounterElement}
    />
  ) : (
    participantCounterElement
  );
}

function ParticipantAccordionItem({
  table,
  collapsible = true,
  noTitle = false,
}: ParticipantAccordionItemProps) {
  const visibleParticipantsCount = table.rows.length;
  const totalParticipantCount = table.num_participants;
  const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;

  const [isActive, setIsActive] = useState(!collapsible || visibleParticipantsCount > 0);
  const handleClick = () => setIsActive(!isActive);

  return (
    <>
      {!noTitle && (
        <AccordionTitle
          active={isActive}
          onClick={collapsible ? handleClick : undefined}
          styleName="accordion-title"
        >
          {collapsible && <Icon name="dropdown" />}
          <p>{table.title || <Translate>Participants</Translate>}</p>
          <ParticipantCounter
            totalCount={totalParticipantCount}
            hiddenCount={hiddenParticipantsCount}
          />
        </AccordionTitle>
      )}
      <AccordionContent active={isActive}>
        <ParticipantTable table={table} />
      </AccordionContent>
    </>
  );
}

export default function ParticipantAccordion({
  published,
  totalParticipantCount,
  tables,
  merged,
}: ParticipantAccordionProps) {
  let infoContent: ReactNode;

  if (!published) {
    infoContent = <Translate>There are no published registrations.</Translate>;
  } else if (totalParticipantCount <= 0) {
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
    <Accordion fluid>
      {tables.map((table: TableObj, i: number) => (
        <ParticipantAccordionItem
          // eslint-disable-next-line react/no-array-index-key
          key={i}
          collapsible={tables.length !== 1}
          table={table}
          noTitle={merged}
        />
      ))}
    </Accordion>
  );
}
