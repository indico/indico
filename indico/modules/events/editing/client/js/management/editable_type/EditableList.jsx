// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import dashboardURL from 'indico-url:event_editing.dashboard';
// import manageEditableTypeListURL from 'indico-url:event_editing.manage_editable_type_list'; Uncomment when we have backend ready

import React, {useState} from 'react';
import {useParams} from 'react-router-dom';
import {Button, Icon, Checkbox, Message, Search} from 'semantic-ui-react';
import {Column, Table, SortDirection, WindowScroller} from 'react-virtualized';
import _ from 'lodash';
import {
  TooltipIfTruncated,
  ManagementPageSubTitle,
  ManagementPageBackButton,
} from 'indico/react/components';
import {useNumericParam} from 'indico/react/util/routing';
import {Translate} from 'indico/react/i18n';
import {EditableType} from '../../models';
import StateIndicator from '../../editing/timeline/StateIndicator';

import './EditableList.module.scss';

export default function EditableList() {
  const list = []; // Replace it with list from server
  const eventId = useNumericParam('confId');
  const {type} = useParams();
  const [sortBy, setSortBy] = useState('id');
  const [sortDirection, setSortDirection] = useState('ASC');
  const [sortedList, setSortedList] = useState(list); // list from server
  const [checked, setChecked] = useState([]);
  const hasCheckedRows = checked.length === 0;
  const title = {
    [EditableType.paper]: Translate.string('List of papers'),
    [EditableType.slides]: Translate.string('List of slides'),
    [EditableType.poster]: Translate.string('List of posters'),
  }[type];
  const columnHeaders = [
    ['id', Translate.string('ID'), 60],
    ['code', Translate.string('Code'), 80],
    ['title', Translate.string('Title'), 600],
    ['status', Translate.string('Status'), 150],
    ['assigned', Translate.string('Assigned'), 400],
  ];

  // eslint-disable-next-line no-shadow
  const _sortList = ({sortBy, sortDirection}) => {
    const newList = _.sortBy(list, [sortBy]);
    if (sortDirection === SortDirection.DESC) {
      newList.reverse();
    }
    return newList;
  };

  // eslint-disable-next-line no-shadow
  const _sort = ({sortBy, sortDirection}) => {
    setSortBy(sortBy);
    setSortDirection(sortDirection);
    setSortedList(_sortList({sortBy, sortDirection}));
  };

  // eslint-disable-next-line react/prop-types
  const renderCell = ({dataKey, rowIndex}) => {
    return (
      <TooltipIfTruncated>
        <div index={rowIndex} styleName="rowcolumn-tooltip" role="gridcell">
          {dataKey === 'assigned' && <Icon name="user outline" />}
          {dataKey === 'status' ? (
            <StateIndicator index={rowIndex} state={sortedList[rowIndex][dataKey]} circular label />
          ) : (
            sortedList[rowIndex][dataKey]
          )}
        </div>
      </TooltipIfTruncated>
    );
  };

  const toggleSelectAll = dataChecked => {
    if (dataChecked) {
      setChecked(sortedList.map(row => row.id));
    } else {
      setChecked([]);
    }
  };

  const toggleSelectRow = dataIndex => {
    const newRow = sortedList[dataIndex].id;
    if (checked.includes(newRow)) {
      setChecked(old => old.filter(row => row !== newRow));
    } else {
      setChecked(old => [...old, newRow]);
    }
  };

  return (
    <>
      <ManagementPageSubTitle title={title} />
      <ManagementPageBackButton url={dashboardURL({confId: eventId})} />
      <div styleName="editable-topbar">
        <div>
          <Button disabled={hasCheckedRows} content={Translate.string('Assign')} />
          <Button disabled={hasCheckedRows} content={Translate.string('Unassign')} />
          <Button disabled={hasCheckedRows} content={Translate.string('Set status')} />
          <Button
            disabled={hasCheckedRows}
            color="blue"
            content={Translate.string('Assign to myself')}
          />
          <Button disabled={hasCheckedRows} content={Translate.string('Download all files')} />
        </div>
        <Search />
      </div>
      {sortedList.length ? (
        <div styleName="editable-list">
          <WindowScroller>
            {({height, isScrolling, onChildScroll, scrollTop}) => (
              <Table
                autoHeight
                width={1000}
                styleName="table"
                height={height}
                isScrolling={isScrolling}
                onScroll={onChildScroll}
                headerHeight={30}
                rowHeight={40}
                sort={_sort}
                sortBy={sortBy}
                sortDirection={sortDirection}
                rowCount={sortedList.length}
                scrollTop={scrollTop}
                rowGetter={({index}) => sortedList[index]}
              >
                <Column
                  disableSort
                  dataKey="checkbox"
                  width={30}
                  headerRenderer={() => (
                    <Checkbox
                      indeterminate={checked.length > 0 && checked.length < sortedList.length}
                      checked={checked.length === sortedList.length}
                      onChange={(e, data) => toggleSelectAll(data.checked)}
                    />
                  )}
                  cellRenderer={({rowIndex}) => (
                    <Checkbox
                      checked={checked.includes(sortedList[rowIndex].id)}
                      onChange={(e, data) => toggleSelectRow(data.index)}
                      index={rowIndex}
                    />
                  )}
                />
                {columnHeaders.map(([key, label, width, extraProps]) => (
                  <Column
                    key={key}
                    dataKey={key}
                    label={label}
                    width={width}
                    {...extraProps}
                    cellRenderer={renderCell}
                  />
                ))}
              </Table>
            )}
          </WindowScroller>
        </div>
      ) : (
        <Message info>
          <Translate>There are no editables yet.</Translate>
        </Message>
      )}
    </>
  );
}
