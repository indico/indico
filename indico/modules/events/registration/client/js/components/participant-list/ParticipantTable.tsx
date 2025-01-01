// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {
  Icon,
  Message,
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHeader,
  TableHeaderCell,
  TableRow,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {ParticipantCountHidden} from './ParticipantSharedTranslations';
import {TableColumnObj, TableObj, TableRowObj} from './types';

import './ParticipantTable.module.scss';

interface ParticipantTableProps {
  table: TableObj;
}

export default function ParticipantTable({table}: ParticipantTableProps) {
  const visibleParticipantsCount = table.rows.length;
  const totalParticipantCount = table.num_participants;
  const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;
  const hasInvisibleParticipants = hiddenParticipantsCount > 0;

  type sortDirectionType = 'ascending' | 'descending' | null;

  const [sortColumn, setSortColumn] = useState<number | string | null>(null);
  const [sortDirection, setSortDirection] = useState<sortDirectionType>(null);
  const [sortedRows, setSortedRows] = useState([...table.rows]);

  const isColumnSortable = (colIndex: number) => {
    const {rows} = table;
    // More conditions could be added, but by that time I hope we have replaced the
    // data structure coming from the back-end, which does not make sense.
    return !rows || !rows.length || !rows[0].columns[colIndex].is_picture;
  };

  const handleSort = (column: number | string | null) => {
    const directions: Record<sortDirectionType, sortDirectionType> = {
      [null as sortDirectionType]: 'ascending',
      ascending: 'descending',
      descending: null,
    };

    const direction: sortDirectionType =
      sortColumn === column ? directions[sortDirection] : 'ascending';

    const sortedData =
      direction === null
        ? [...table.rows]
        : [...sortedRows].sort((a, b) => {
            const comparedVals = [a, b].map(el =>
              typeof column === 'string' ? el[column] : el.columns[column].text
            );

            let sortResult;

            if (comparedVals[0] === comparedVals[1]) {
              return 0;
            } else if (comparedVals.every(el => typeof el === 'boolean')) {
              sortResult = comparedVals[0] > comparedVals[1] ? -1 : 1;
            } else {
              sortResult = comparedVals[0].localeCompare(comparedVals[1]);
            }

            return sortResult * (direction === 'ascending' ? 1 : -1);
          });

    setSortColumn(column);
    setSortDirection(direction);
    setSortedRows(sortedData);
  };

  return visibleParticipantsCount > 0 ? (
    <Table fixed celled sortable>
      <TableHeader>
        <TableRow>
          {table.show_checkin && ( // For checkin status
            <TableHeaderCell
              styleName="participant-table-row icon-cell"
              onClick={() => handleSort('checked_in')}
              sorted={sortColumn === 'checked_in' ? sortDirection : undefined}
              title={Translate.string('Check-in status')}
            >
              <Icon name="ticket" />
            </TableHeaderCell>
          )}
          {table.headers.map((headerText: string, i: number) => {
            const isSortable = isColumnSortable(i);

            return (
              <TableHeaderCell
                // eslint-disable-next-line react/no-array-index-key
                key={i}
                styleName={`participant-table-row ${isSortable ? '' : 'unsortable'}`}
                onClick={isSortable ? () => handleSort(i) : undefined}
                sorted={isSortable && sortColumn === i ? sortDirection : undefined}
                title={headerText}
              >
                <p>{headerText}</p>
              </TableHeaderCell>
            );
          })}
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedRows.map((row: TableRowObj) => (
          <TableRow key={row.id}>
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
                {col.is_picture ? (
                  col.text ? (
                    <img src={col.text} alt="" styleName="cell-img" />
                  ) : (
                    <div styleName="cell-img" />
                  )
                ) : (
                  col.text
                )}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
      {hasInvisibleParticipants && (
        <TableFooter fullWidth>
          <TableRow>
            <TableHeaderCell colSpan={table.headers.length + Number(table.show_checkin)}>
              <ParticipantCountHidden count={hiddenParticipantsCount} />
            </TableHeaderCell>
          </TableRow>
        </TableFooter>
      )}
    </Table>
  ) : (
    <Message>
      {totalParticipantCount > 0 ? (
        <ParticipantCountHidden count={hiddenParticipantsCount} />
      ) : (
        <Translate>No participants registered.</Translate>
      )}
    </Message>
  );
}
