// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import dashboardURL from 'indico-url:event_editing.dashboard';
import editableListURL from 'indico-url:event_editing.api_editable_list';
import editablesArchiveURL from 'indico-url:event_editing.api_prepare_editables_archive';

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {useParams} from 'react-router-dom';
import {Button, Icon, Loader, Checkbox, Message, Search} from 'semantic-ui-react';
import {Column, Table, SortDirection, WindowScroller} from 'react-virtualized';
import _ from 'lodash';
import {
  TooltipIfTruncated,
  ManagementPageSubTitle,
  ManagementPageBackButton,
} from 'indico/react/components';
import {useNumericParam} from 'indico/react/util/routing';
import {Translate} from 'indico/react/i18n';
import {useIndicoAxios} from 'indico/react/hooks';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {userPropTypes} from '../../editing/timeline/util';
import {EditableType} from '../../models';
import StateIndicator from '../../editing/timeline/StateIndicator';

import './EditableList.module.scss';

export default function EditableList() {
  const eventId = useNumericParam('confId');
  const {type} = useParams();
  const {data, loading: isLoadingEditableList, lastData} = useIndicoAxios({
    url: editableListURL({confId: eventId, type}),
    camelize: true,
    trigger: eventId,
  });
  const editableList = data || lastData;
  if (isLoadingEditableList && !lastData) {
    return <Loader inline="centered" active />;
  } else if (!editableList) {
    return null;
  }
  const codePresent = Object.values(editableList).some(c => c.code);
  return (
    <EditableListDisplay
      editableList={editableList}
      codePresent={codePresent}
      editableType={type}
      eventId={eventId}
    />
  );
}

function EditableListDisplay({editableList, codePresent, editableType, eventId}) {
  const [sortBy, setSortBy] = useState('friendly_id');
  const [sortDirection, setSortDirection] = useState('ASC');
  const [sortedList, setSortedList] = useState(editableList);
  const [checked, setChecked] = useState([]);
  const editables = sortedList.filter(x => x.editable);
  const hasCheckedEditables = checked.length > 0;
  const title = {
    [EditableType.paper]: Translate.string('List of papers'),
    [EditableType.slides]: Translate.string('List of slides'),
    [EditableType.poster]: Translate.string('List of posters'),
  }[editableType];
  const columnHeaders = [
    ['friendlyId', Translate.string('ID'), 60],
    ...(codePresent ? [['code', Translate.string('Code'), 80]] : []),
    ['title', Translate.string('Title'), 600],
    ['revision', Translate.string('Rev.'), 80],
    ['status', Translate.string('Status'), 200],
    ['editor', Translate.string('Editor'), 400],
  ];

  const sortEditor = contribution =>
    contribution.editable &&
    contribution.editable.editor &&
    contribution.editable.editor.fullName.toLowerCase();
  const sortStatus = contribution =>
    contribution.editable && contribution.editable.state.toLowerCase();
  const sortTitle = contribution => contribution.title.toLowerCase();

  const sortFuncs = {
    title: sortTitle,
    revision: contribution => contribution.editable && contribution.editable.revisionCount,
    status: sortStatus,
    editor: sortEditor,
  };

  // eslint-disable-next-line no-shadow
  const _sortList = ({sortBy, sortDirection}) => {
    const fn = sortFuncs[sortBy] || (x => x);
    const newList = _.sortBy(editableList, fn);
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

  const renderCode = code => code || Translate.string('n/a');
  const renderEditor = editable => {
    return editable && editable.editor ? (
      <div>
        <Icon name="user outline" />
        {editable.editor.fullName}
      </div>
    ) : (
      <div />
    );
  };
  // eslint-disable-next-line no-shadow
  const renderTitle = (title, index) => {
    return sortedList[index].editable ? (
      <a href={sortedList[index].editable.timelineURL}>{title}</a>
    ) : (
      <div>{title}</div>
    );
  };
  const renderStatus = editable => {
    return <StateIndicator state={editable ? editable.state : 'not_submitted'} circular label />;
  };
  const renderFuncs = {
    title: renderTitle,
    code: renderCode,
    revision: editable => (editable ? editable.revisionCount : ''),
    status: renderStatus,
    editor: renderEditor,
  };

  // eslint-disable-next-line react/prop-types
  const renderCell = ({dataKey, rowIndex}) => {
    let data = sortedList[rowIndex][dataKey];
    if (['editor', 'revision', 'status'].includes(dataKey)) {
      data = sortedList[rowIndex].editable;
    }
    const fn = renderFuncs[dataKey] || (x => x);
    return (
      <TooltipIfTruncated>
        <div
          index={rowIndex}
          styleName="rowcolumn-tooltip"
          role="gridcell"
          style={dataKey === 'title' ? {display: 'block'} : {}}
        >
          {fn(data, rowIndex)}
        </div>
      </TooltipIfTruncated>
    );
  };

  const toggleSelectAll = dataChecked => {
    if (dataChecked) {
      setChecked(editables.map(row => row.editable.id));
    } else {
      setChecked([]);
    }
  };

  const toggleSelectRow = dataIndex => {
    const newRow = sortedList[dataIndex].editable.id;
    if (checked.includes(newRow)) {
      setChecked(old => old.filter(row => row !== newRow));
    } else {
      setChecked(old => [...old, newRow]);
    }
  };

  const downloadAllFiles = async () => {
    let response;
    try {
      response = await indicoAxios.post(
        editablesArchiveURL({confId: eventId, type: editableType}),
        {editables: checked}
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }

    location.href = response.data.download_url;
  };

  return (
    <>
      <ManagementPageSubTitle title={title} />
      <ManagementPageBackButton url={editableTypeURL({confId: eventId, type: editableType})} />
      <div styleName="editable-topbar">
        <div>
          <Button disabled={!hasCheckedEditables} content={Translate.string('Assign')} />
          <Button disabled={!hasCheckedEditables} content={Translate.string('Unassign')} />
          <Button disabled={!hasCheckedEditables} content={Translate.string('Set status')} />
          <Button
            disabled={!hasCheckedEditables}
            color="blue"
            content={Translate.string('Assign to myself')}
          />
          <Button
            disabled={!hasCheckedEditables}
            content={Translate.string('Download all files')}
            onClick={downloadAllFiles}
          />
        </div>
        <Search disabled={!sortedList.length} />
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
                      indeterminate={checked.length > 0 && checked.length < editables.length}
                      checked={checked.length === editables.length}
                      onChange={(e, data) => toggleSelectAll(data.checked)}
                    />
                  )}
                  cellRenderer={({rowIndex}) => (
                    <Checkbox
                      disabled={!sortedList[rowIndex].editable}
                      checked={
                        sortedList[rowIndex].editable
                          ? checked.includes(sortedList[rowIndex].editable.id)
                          : false
                      }
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

EditableListDisplay.propTypes = {
  editableList: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      friendlyId: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      code: PropTypes.string.isRequired,
      editable: PropTypes.shape({
        id: PropTypes.number,
        editor: PropTypes.shape(userPropTypes),
        state: PropTypes.string,
        type: PropTypes.oneOf(Object.values(EditableType)),
        timelineURL: PropTypes.string,
      }),
    })
  ).isRequired,
  codePresent: PropTypes.bool.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
  eventId: PropTypes.number.isRequired,
};
