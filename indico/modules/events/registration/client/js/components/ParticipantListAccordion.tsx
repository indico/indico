// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {HTMLAttributes, ReactNode, useState} from 'react';
import {
  AccordionTitle,
  AccordionContent,
  Accordion,
  Icon,
  TableRow,
  TableHeaderCell,
  TableHeader,
  TableCell,
  TableBody,
  Table,
  TableFooter,
  Popup,
  Message,
} from 'semantic-ui-react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import './ParticipantListAccordion.module.scss';

interface TableColumnObj {
  id: number;
  text: string;
  is_picture: boolean;
}

interface TableRowObj {
  id: number;
  checked_in: boolean;
  columns: TableColumnObj[];
}

interface TableObj {
  headers: string[];
  rows: TableRowObj[];
  num_participants: number;
  show_checkin: boolean;
  title?: string;
}

interface ParticipantListAccordionProps {
  tables: TableObj[];
}

interface AccordionParticipantsItemProps {
  index: number;
  table: TableObj;
  children?: ReactNode;
  collapsible?: boolean;
}

interface ParticipantCounterProps extends HTMLAttributes<HTMLSpanElement> {
  totalCount: number;
  hiddenCount: number;
  styleName?: string;
}

function ParticipantCountTranslationHidden({count}: {count: number}) {
  return (
    <PluralTranslate count={count}>
      <Singular>
        <Param name="count" value={count} /> participant registered anonymously.
      </Singular>
      <Plural>
        <Param name="count" value={count} /> participants registered anonymously.
      </Plural>
    </PluralTranslate>
  );
}

function ParticipantCounter({
  totalCount,
  hiddenCount,
  styleName = '',
  ...props
}: ParticipantCounterProps) {
  const participantCounterElement = (
    <span>
      {totalCount} <Icon name="user" />
    </span>
  );

  return hiddenCount > 0 ? (
    <div className={styleName} {...props}>
      <Popup
        position="left center"
        content={<ParticipantCountTranslationHidden count={hiddenCount} />}
        trigger={participantCounterElement}
      />
    </div>
  ) : (
    participantCounterElement
  );
}

function ParticipantTable({table}: {table: TableObj}) {
  const visibleParticipantsCount = table.rows.length;
  const totalParticipantCount = table.num_participants;
  const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;
  const hasInvisibleParticipants = hiddenParticipantsCount > 0;

  type sortDirectionType = 'ascending' | 'descending' | null;

  const [sortColumn, setSortColumn] = useState<number | null>(null);
  const [sortDirection, setSortDirection] = useState<sortDirectionType>(null);
  const [sortedRows, setSortedRows] = useState([...table.rows]);

  const handleSort = (columnIndex: number) => {
    const directions: Record<sortDirectionType, sortDirectionType> = {
      [null as sortDirectionType]: 'ascending',
      ascending: 'descending',
      descending: null,
    };

    const direction: sortDirectionType =
      sortColumn === columnIndex ? directions[sortDirection] : 'ascending';

    const sortedData =
      direction === null
        ? [...table.rows]
        : [...sortedRows].sort((a, b) => {
            const textA = a.columns[columnIndex].text.toLowerCase();
            const textB = b.columns[columnIndex].text.toLowerCase();

            if (textA < textB) {
              return direction === 'ascending' ? -1 : 1;
            } else if (textA > textB) {
              return direction === 'ascending' ? 1 : -1;
            }

            return 0;
          });

    setSortColumn(columnIndex);
    setSortDirection(direction);
    setSortedRows(sortedData);
  };

  return visibleParticipantsCount > 0 ? (
    <Table fixed celled sortable className="table">
      <TableHeader>
        <TableRow className="table-row">
          {table.show_checkin && ( // For checkin status
            <TableHeaderCell width={1} textAlign="center">
              <Icon name="ticket" />
            </TableHeaderCell>
          )}
          {table.headers.map((headerText: string, i: number) => (
            <TableHeaderCell
              // eslint-disable-next-line react/no-array-index-key
              key={i}
              sorted={sortColumn === i ? sortDirection : undefined}
              onClick={() => handleSort(i)}
              title={headerText}
            >
              {headerText}
            </TableHeaderCell>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedRows.map((row: TableRowObj) => (
          <TableRow key={row.id} className="table-row">
            {table.show_checkin && (
              <TableCell textAlign="center">
                {row.checked_in ? (
                  <Icon name="check" color="green" />
                ) : (
                  <Icon name="close" color="red" />
                )}
              </TableCell>
            )}
            {row.columns.map((col: TableColumnObj, i: number) => (
              // eslint-disable-next-line react/no-array-index-key
              <TableCell key={i} title={col.text}>
                {col.is_picture && col.text ? (
                  <img src={col.text} className="cell-img" />
                ) : (
                  col.text
                )}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
      {hasInvisibleParticipants && (
        <TableFooter>
          <TableRow>
            <TableHeaderCell colSpan={table.headers.length}>
              <ParticipantCountTranslationHidden count={hiddenParticipantsCount} />
            </TableHeaderCell>
          </TableRow>
        </TableFooter>
      )}
    </Table>
  ) : (
    <Message>
      {totalParticipantCount > 0 ? (
        <ParticipantCountTranslationHidden count={hiddenParticipantsCount} />
      ) : (
        <Translate>No participants registered</Translate>
      )}
    </Message>
  );
}

function AccordionParticipantsItem({
  index,
  table,
  children = null,
  collapsible = true,
}: AccordionParticipantsItemProps) {
  const visibleParticipantsCount = table.rows.length;
  const totalParticipantCount = table.num_participants;
  const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;

  const [isActive, setIsActive] = useState(!collapsible || visibleParticipantsCount > 0);
  const handleClick = () => setIsActive(!isActive);

  return (
    <>
      <AccordionTitle
        active={isActive}
        onClick={collapsible ? handleClick : undefined}
        styleName="title"
      >
        {collapsible && <Icon name="dropdown" />}
        <p>{table.title || <Translate>Participants</Translate>}kasdfkjlsafkjsahdfkjsadhfklsdahfkhfjhfdkasdfkjlsafkjsahdfkjsadhfklsdahfkhfjhfdkasdfkjlsafkjsahdfkjsadhfklsdahfkhfjhfdkasdfkjlsafkjsahdfkjsadhfklsdahfkhfjhfd</p>
        <ParticipantCounter
          styleName="participants-count-wrapper"
          totalCount={totalParticipantCount}
          hiddenCount={hiddenParticipantsCount}
        />
      </AccordionTitle>
      <AccordionContent active={isActive} key={`c${index}`}>
        {children || <ParticipantTable table={table} />}
      </AccordionContent>
    </>
  );
}

export default function ParticipantListAccordion({tables}: ParticipantListAccordionProps) {
  return (
    <Accordion styled fluid>
      {tables.length === 1 ? ( // Case of no participants is handled in Jinja now
        <AccordionParticipantsItem table={tables[0]} index={1} collapsible={false} />
      ) : (
        tables.map((table: TableObj, i: number) => (
          // eslint-disable-next-line react/no-array-index-key
          <AccordionParticipantsItem key={i} index={i} table={table} />
        ))
      )}
    </Accordion>
  );
}
