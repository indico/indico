// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableTypeURL from 'indico-url:event_editing.manage_editable_type';
import editorsURL from 'indico-url:event_editing.api_editable_type_editors';
import editableListURL from 'indico-url:event_editing.api_editable_list';
import editablesArchiveURL from 'indico-url:event_editing.api_prepare_editables_archive';
import assignEditorURL from 'indico-url:event_editing.api_assign_editor';
import assignSelfEditorURL from 'indico-url:event_editing.api_assign_myself';
import unassignEditorURL from 'indico-url:event_editing.api_unassign_editor';

import React, {useState, useMemo} from 'react';
import PropTypes from 'prop-types';
import {useParams} from 'react-router-dom';
import {Button, Icon, Input, Loader, Checkbox, Message, Dropdown} from 'semantic-ui-react';
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
import {camelizeKeys} from 'indico/utils/case';
import Palette from 'indico/utils/palette';
import {userPropTypes} from '../../editing/timeline/util';
import {EditableType} from '../../models';
import StateIndicator from '../../editing/timeline/StateIndicator';

import './EditableList.module.scss';

export default function EditableList() {
  const eventId = useNumericParam('confId');
  const {type} = useParams();
  const {data: contribList, loading: isLoadingContribList} = useIndicoAxios({
    url: editableListURL({confId: eventId, type}),
    camelize: true,
    trigger: [eventId, type],
  });
  const {data: editors, loading: isLoadingEditors} = useIndicoAxios({
    url: editorsURL({confId: eventId, type}),
    camelize: true,
    trigger: [eventId, type],
  });
  if (isLoadingContribList || isLoadingEditors) {
    return <Loader inline="centered" active />;
  } else if (!contribList || !editors) {
    return null;
  }
  const codePresent = Object.values(contribList).some(c => c.code);
  return (
    <EditableListDisplay
      initialContribList={contribList}
      codePresent={codePresent}
      editableType={type}
      eventId={eventId}
      editors={editors}
    />
  );
}

function EditableListDisplay({initialContribList, codePresent, editableType, eventId, editors}) {
  const [sortBy, setSortBy] = useState('friendly_id');
  const [sortDirection, setSortDirection] = useState('ASC');

  const [contribList, setContribList] = useState(initialContribList);
  const [sortedList, setSortedList] = useState(contribList);
  const contribsWithEditables = contribList.filter(x => x.editable);
  const contribIdSet = new Set(contribsWithEditables.map(x => x.id));
  const [filteredSet, setFilteredSet] = useState(new Set(contribList.map(e => e.id)));
  const [searchValue, setSearchValue] = useState('');

  const [checked, setChecked] = useState([]);
  const hasCheckedContribs = checked.length > 0;
  const checkedSet = new Set(checked);
  const checkedContribsWithEditables = contribsWithEditables.filter(x =>
    checkedSet.has(x.editable.id)
  );
  const [activeRequest, setActiveRequest] = useState(null);

  const editorOptions = useMemo(
    () =>
      _.sortBy(editors, 'fullName').map(e => ({
        key: e.identifier,
        icon: 'user',
        text: e.fullName,
        value: e.identifier,
      })),
    [editors]
  );

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
  const _sortList = (sortBy, sortDirection, filteredResults) => {
    const fn = sortFuncs[sortBy] || (x => x);
    const newList = _.sortBy(contribList, fn);
    if (sortDirection === SortDirection.DESC) {
      newList.reverse();
    }
    const matching = newList.filter(e => filteredResults.has(e.id));
    const notMatching = newList.filter(e => !filteredResults.has(e.id));
    return [...matching, ...notMatching];
  };

  // eslint-disable-next-line no-shadow
  const _sort = ({sortBy, sortDirection}) => {
    setSortBy(sortBy);
    setSortDirection(sortDirection);
    setSortedList(_sortList(sortBy, sortDirection, filteredSet));
  };

  const patchList = updatedEditables => {
    updatedEditables = new Map(updatedEditables.map(x => [x.id, x]));
    const _mapper = contrib => {
      if (!contrib.editable || !updatedEditables.has(contrib.editable.id)) {
        return contrib;
      }
      return {...contrib, editable: updatedEditables.get(contrib.editable.id)};
    };
    setContribList(list => list.map(_mapper));
    setSortedList(list => list.map(_mapper));
  };

  const setFilter = value => {
    setSearchValue(value);
    value = value.toLowerCase().trim();

    const isMatch = result => {
      if (!value) {
        return true;
      }
      const match = value.match(/^#(\d+)$/);
      if (match) {
        return result.friendlyId === +match[1];
      }
      return (
        result.title.toLowerCase().includes(value) ||
        (result.editable &&
          result.editable.editor &&
          result.editable.editor.fullName.toLowerCase().includes(value)) ||
        (result.code && result.code.toLowerCase().includes(value))
      );
    };
    const filteredResults = new Set(contribList.filter(isMatch).map(e => e.id));
    setFilteredSet(filteredResults);
    setSortedList(_sortList(sortBy, sortDirection, filteredResults));
    setChecked(
      contribsWithEditables
        .filter(row => checkedSet.has(row.editable.id) && filteredResults.has(row.id))
        .map(row => row.editable.id)
    );
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
  const renderStatus = (editable, rowIndex) => {
    return (
      <StateIndicator
        state={editable ? editable.state : 'not_submitted'}
        circular
        label
        monochrome={!filteredSet.has(sortedList[rowIndex].id)}
      />
    );
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
      setChecked(
        contribsWithEditables.filter(row => filteredSet.has(row.id)).map(row => row.editable.id)
      );
    } else {
      setChecked([]);
    }
  };

  const toggleSelectRow = dataIndex => {
    const newId = sortedList[dataIndex].editable.id;
    if (checkedSet.has(newId)) {
      setChecked(old => old.filter(id => id !== newId));
    } else {
      setChecked(old => [...old, newId]);
    }
  };

  const checkedEditablesRequest = async (urlFunc, data = {}) => {
    let response;
    try {
      response = await indicoAxios.post(urlFunc({confId: eventId, type: editableType}), {
        editables: checked,
        ...data,
      });
    } catch (error) {
      handleAxiosError(error);
      return null;
    } finally {
      setActiveRequest(null);
    }

    return camelizeKeys(response.data);
  };

  const downloadAllFiles = async () => {
    setActiveRequest('download');
    const rv = await checkedEditablesRequest(editablesArchiveURL);
    if (rv) {
      location.href = rv.downloadURL;
    }
  };

  const updateCheckedEditablesRequest = async (type, urlFunc, data = {}) => {
    setActiveRequest(type);
    const rv = await checkedEditablesRequest(urlFunc, data);
    if (rv) {
      patchList(rv);
    }
  };

  const assignEditor = editor => {
    updateCheckedEditablesRequest('assign', assignEditorURL, {editor});
  };

  const assignSelfEditor = () => {
    updateCheckedEditablesRequest('assign-self', assignSelfEditorURL);
  };

  const unassignEditor = async () => {
    updateCheckedEditablesRequest('unassign', unassignEditorURL);
  };

  return (
    <>
      <ManagementPageSubTitle title={title} />
      <ManagementPageBackButton url={editableTypeURL({confId: eventId, type: editableType})} />
      <div styleName="editable-topbar">
        <div>
          <Button.Group>
            <Dropdown
              disabled={!hasCheckedContribs || !editors.length || !!activeRequest}
              options={editorOptions}
              scrolling
              icon={null}
              value={null}
              selectOnBlur={false}
              selectOnNavigation={false}
              onChange={(evt, {value}) => assignEditor(value)}
              trigger={
                <Button icon loading={activeRequest === 'assign'}>
                  <Translate>Assign</Translate>
                  <Icon name="caret down" />
                </Button>
              }
            />
            <Button
              disabled={!hasCheckedContribs || !!activeRequest}
              color="blue"
              content={Translate.string('Assign to myself')}
              onClick={assignSelfEditor}
              loading={activeRequest === 'assign-self'}
            />
            <Button
              disabled={
                !checkedContribsWithEditables.some(x => x.editable.editor) || !!activeRequest
              }
              content={Translate.string('Unassign')}
              onClick={unassignEditor}
              loading={activeRequest === 'unassign'}
            />
          </Button.Group>{' '}
          <Button
            disabled={!hasCheckedContribs || !!activeRequest}
            content={Translate.string('Download all files')}
            onClick={downloadAllFiles}
            loading={activeRequest === 'download'}
          />
        </div>
        <Input
          placeholder={Translate.string('Enter #id or search string')}
          onChange={(evt, {value}) => setFilter(value)}
          value={searchValue}
          icon={
            <Icon
              name="close"
              link
              onClick={() => setFilter('')}
              style={searchValue ? {} : {display: 'none'}}
            />
          }
        />
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
                rowStyle={({index}) =>
                  index !== -1 && !filteredSet.has(sortedList[index].id)
                    ? {backgroundColor: Palette.pastelGray, opacity: '60%'}
                    : {}
                }
              >
                <Column
                  disableSort
                  dataKey="checkbox"
                  width={30}
                  headerRenderer={() => (
                    <Checkbox
                      indeterminate={
                        checked.length > 0 &&
                        checked.length < [...filteredSet].filter(x => contribIdSet.has(x)).length
                      }
                      checked={
                        checked.length > 0 &&
                        checked.length === [...filteredSet].filter(x => contribIdSet.has(x)).length
                      }
                      onChange={(e, data) => toggleSelectAll(data.checked)}
                      disabled={!!activeRequest}
                    />
                  )}
                  cellRenderer={({rowIndex}) =>
                    sortedList[rowIndex].editable && (
                      <Checkbox
                        disabled={!!activeRequest || !filteredSet.has(sortedList[rowIndex].id)}
                        checked={
                          sortedList[rowIndex].editable
                            ? checkedSet.has(sortedList[rowIndex].editable.id)
                            : false
                        }
                        onChange={(e, data) => toggleSelectRow(data.index)}
                        index={rowIndex}
                      />
                    )
                  }
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
  initialContribList: PropTypes.arrayOf(
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
  editors: PropTypes.arrayOf(PropTypes.shape(userPropTypes)).isRequired,
  codePresent: PropTypes.bool.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
  eventId: PropTypes.number.isRequired,
};
