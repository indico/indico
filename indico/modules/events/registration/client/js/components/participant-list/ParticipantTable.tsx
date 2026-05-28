// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useMemo, useState} from 'react';
import {
  Icon,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Pagination,
  Dropdown,
  Input,
  Popup,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {ParticipantCountHidden} from './ParticipantSharedTranslations';
import {TableColumnObj, TableObj, TableRowObj} from './types';
import './ParticipantTable.module.scss';

type SortDirectionType = 'ascending' | 'descending' | null;
export type PerPageOptions = number | 'all';

interface ParticipantTableProps {
  table: TableObj;
  merged?: boolean;
  search: string;
  setSearch: (val: string) => void;
  perPage: PerPageOptions;
  setPerPage: (val: PerPageOptions) => void;
  currentPage: number;
  setCurrentPage: (val: number) => void;
}

export default function ParticipantTable({
  table,
  merged = true,
  search,
  setSearch,
  perPage,
  setPerPage,
  currentPage,
  setCurrentPage,
}: ParticipantTableProps) {
  const visibleParticipantsCount = table.rows.length;
  const totalParticipantsCount = table.num_participants;
  const hiddenParticipantsCount = table.num_anonymous_participants;

  const [sortColumn, setSortColumn] = useState<number | string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirectionType>(null);

  function filterRows(rows: TableRowObj[], searchString: string): TableRowObj[] {
    const query = searchString.trim().toLowerCase();
    if (!query) {
      return rows;
    }

    const exactSearchRegex = /^(['"]).*\1$/;
    if (exactSearchRegex.test(query)) {
      const value = query.slice(1, -1).toLowerCase();
      return rows.filter(row => row.columns.some(col => col.text?.toLowerCase() === value));
    }

    return rows.filter(row =>
      row.columns.some(col =>
        col.text
          ?.toLowerCase()
          .normalize('NFD')
          .replace(/\p{Diacritic}/gu, '')
          .includes(query)
      )
    );
  }

  function sortRows(
    rows: TableRowObj[],
    column: number | string | null,
    direction: SortDirectionType
  ): TableRowObj[] {
    if (direction === null || column === null) {
      return rows;
    }

    return [...rows].sort((a, b) => {
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
  }

  const isColumnSortable = (colIndex: number) => {
    const {rows} = table;
    // More conditions could be added, but by that time I hope we have replaced the
    // data structure coming from the back-end, which does not make sense.
    return !rows || !rows.length || !rows[0].columns[colIndex].is_picture;
  };

  const handleSort = (column: number | string | null) => {
    const nextDirection: Record<SortDirectionType, SortDirectionType> = {
      [null as SortDirectionType]: 'ascending',
      ascending: 'descending',
      descending: null,
    };

    const direction: SortDirectionType =
      sortColumn === column ? nextDirection[sortDirection] : 'ascending';

    setSortColumn(column);
    setSortDirection(direction);
    setCurrentPage(1);
  };

  const processedRows = useMemo(() => {
    let rows = filterRows(table.rows, search);
    rows = sortRows(rows, sortColumn, sortDirection);

    return rows;
  }, [table.rows, search, sortColumn, sortDirection]);

  const totalPages = perPage === 'all' ? 1 : Math.ceil(processedRows.length / perPage);
  const perPageOptions = [25, 50, 100, 'all'];

  const paginatedRows = useMemo(() => {
    if (perPage === 'all') {
      return processedRows;
    }

    const start = (currentPage - 1) * perPage;
    const end = start + perPage;

    return processedRows.slice(start, end);
  }, [processedRows, currentPage, perPage]);

  return visibleParticipantsCount > 0 ? (
    <>
      {merged && hiddenParticipantsCount > 0 && (
        <div styleName="merged-view-hidden-participants-count">
          <ParticipantCountHidden
            count={totalParticipantsCount}
            countHidden={hiddenParticipantsCount}
            displayTotal={false}
          />
        </div>
      )}
      <section styleName="participant-list-top">
        <div>
          Rows per page:
          <Dropdown
            selection
            compact
            floating
            styleName="participant-list-dropdown"
            options={perPageOptions.map(n => ({
              key: n,
              value: n,
              text: n,
            }))}
            value={perPage}
            onChange={(e, {value}) => {
              setPerPage(value as PerPageOptions);
              setCurrentPage(1);
            }}
          />
        </div>
        <div>
          <Popup
            content={
              <Translate>
                You can search for an exact match by wrapping the query in quotes (e.g. "John Doe")
              </Translate>
            }
            trigger={<Icon name="question circle" styleName="search-hint" />}
          />
          <Input
            value={search}
            onChange={(e, {value}) => {
              setSearch(value);
              setCurrentPage(1);
            }}
            icon={<Icon name="search" />}
            placeholder={Translate.string('Search participants')}
          />
        </div>
      </section>
      <Table fixed celled sortable>
        <TableHeader>
          <TableRow>
            {table.show_checkin && (
              <TableHeaderCell
                styleName="participant-table-header icon-cell"
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
                  styleName={`participant-table-header ${isSortable ? '' : 'unsortable'}`}
                  onClick={isSortable ? () => handleSort(i) : undefined}
                  sorted={isSortable && sortColumn === i ? sortDirection : undefined}
                  title={headerText}
                  content={headerText}
                />
              );
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {paginatedRows.length > 0 ? (
            paginatedRows.map((row: TableRowObj) => (
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
                        <img src={col.text} styleName="cell-img" />
                      ) : (
                        <div styleName="cell-img" />
                      )
                    ) : (
                      col.text
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell
                style={{textAlign: 'center'}}
                colSpan={table.headers.length + (table.show_checkin ? 1 : 0)}
              >
                <Translate>No participants found.</Translate>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      {totalPages > 1 && (
        <section styleName="participant-list-pagination-wrapper">
          <Pagination
            styleName="participant-list-pagination"
            activePage={currentPage}
            onPageChange={(e, {activePage}) => setCurrentPage(Number(activePage))}
            totalPages={totalPages}
            ellipsisItem={null}
            firstItem={{
              content: <Icon name="angle double left" />,
              icon: true,
              disabled: currentPage === 1,
            }}
            lastItem={{
              content: <Icon name="angle double right" />,
              icon: true,
              disabled: currentPage === totalPages,
            }}
            boundaryRange={0}
            siblingRange={4}
            prevItem={{
              content: <Icon name="angle left" />,
              icon: true,
              disabled: currentPage === 1,
            }}
            nextItem={{
              content: <Icon name="angle right" />,
              icon: true,
              disabled: currentPage === totalPages,
            }}
          />{' '}
        </section>
      )}
    </>
  ) : (
    <ParticipantCountHidden
      count={totalParticipantsCount}
      countHidden={hiddenParticipantsCount}
      displayTotal={false}
    />
  );
}
