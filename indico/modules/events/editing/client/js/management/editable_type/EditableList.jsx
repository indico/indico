// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import assignEditorURL from 'indico-url:event_editing.api_assign_editor';
import assignSelfEditorURL from 'indico-url:event_editing.api_assign_myself';
import editableListURL from 'indico-url:event_editing.api_editable_list';
import editorsURL from 'indico-url:event_editing.api_editable_type_editors';
import canAssignSelfURL from 'indico-url:event_editing.api_editor_self_assign_allowed';
import editablesArchiveURL from 'indico-url:event_editing.api_prepare_editables_archive';
import unassignEditorURL from 'indico-url:event_editing.api_unassign_editor';
import editableTypeURL from 'indico-url:event_editing.manage_editable_type';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState, useMemo} from 'react';
import {useParams, Link} from 'react-router-dom';
import {Column, Table, SortDirection, WindowScroller} from 'react-virtualized';
import {Button, Icon, Loader, Checkbox, Message, Dropdown} from 'semantic-ui-react';

import {
  TooltipIfTruncated,
  ManagementPageSubTitle,
  ManagementPageBackButton,
  ListFilter,
} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import Palette from 'indico/utils/palette';

import StateIndicator from '../../editing/timeline/StateIndicator';
import {userPropTypes} from '../../editing/timeline/util';
import {EditableType, GetNextEditableTitles} from '../../models';

import NextEditable from './NextEditable';

import './EditableList.module.scss';

export default function EditableList({management}) {
  const eventId = useNumericParam('event_id');
  const {type} = useParams();
  const {data: contribList, loading: isLoadingContribList} = useIndicoAxios({
    url: editableListURL({event_id: eventId, type}),
    camelize: true,
    trigger: [eventId, type],
  });
  const {data: editors, loading: isLoadingEditors} = useIndicoAxios({
    url: editorsURL({event_id: eventId, type}),
    camelize: true,
    trigger: [eventId, type],
    forceDispatchEffect: () => management,
  });
  const {data: canAssignSelf, loading: isLoadingCanAssignSelf} = useIndicoAxios({
    url: canAssignSelfURL({event_id: eventId, type}),
    trigger: [eventId, type],
    forceDispatchEffect: () => !management,
  });

  if (isLoadingContribList || isLoadingEditors || isLoadingCanAssignSelf) {
    return <Loader inline="centered" active />;
  } else if (!contribList || (management && !editors)) {
    return null;
  }
  const codePresent = Object.values(contribList).some(c => c.code);
  return (
    <EditableListDisplay
      initialContribList={contribList}
      codePresent={codePresent}
      editableType={type}
      eventId={eventId}
      editors={management ? editors : []}
      management={management}
      canAssignSelf={management ? false : canAssignSelf}
    />
  );
}

EditableList.propTypes = {
  management: PropTypes.bool,
};

EditableList.defaultProps = {
  management: true,
};

function EditableListDisplay({
  initialContribList,
  codePresent,
  editableType,
  eventId,
  editors,
  management,
  canAssignSelf,
}) {
  const [sortBy, setSortBy] = useState('friendly_id');
  const [sortDirection, setSortDirection] = useState('ASC');

  const [contribList, setContribList] = useState(initialContribList);
  const [sortedList, setSortedList] = useState(contribList);
  const contribsWithEditables = contribList.filter(x => x.editable);
  const contribIdSet = new Set(contribsWithEditables.map(x => x.id));
  const [filteredSet, setFilteredSet] = useState(new Set(contribList.map(e => e.id)));
  const [selfAssignModalVisible, setSelfAssignModalVisible] = useState(false);

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

  const filterOptions = useMemo(
    () => [
      {
        key: 'state',
        text: Translate.string('Status'),
        options: [
          {value: 'accepted', text: Translate.string('Accepted'), exclusive: true},
          {value: 'ready_for_review', text: Translate.string('Ready for review')},
          {value: 'not_submitted', text: Translate.string('Not submitted')},
        ],
        isMatch: (contrib, selectedOptions) =>
          (contrib.c.editable && selectedOptions.includes(contrib.c.editable.state)) ||
          (selectedOptions.includes('not_submitted') && !contrib.c.editable),
      },
      {
        key: 'editor',
        text: Translate.string('Editor'),
        options: _.uniqBy(
          contribsWithEditables.map(c => c.editable.editor).filter(x => x),
          'id'
        ).map(({identifier, fullName}) => ({
          value: identifier,
          text: fullName,
        })),
        isMatch: (contrib, selectedOptions) =>
          contrib.c.editable &&
          contrib.c.editable.editor &&
          selectedOptions.includes(contrib.c.editable.editor.identifier),
      },
      {
        key: 'code',
        text: Translate.string('Program code'),
        options: _.uniq(contribList.map(c => c.code).filter(x => x)).map(code => ({
          value: code,
          text: code,
        })),
        isMatch: (contrib, selectedOptions) => selectedOptions.includes(contrib.c.code),
      },
      {
        key: 'keywords',
        text: Translate.string('Keywords'),
        options: _.uniq(_.flatten(contribList.map(c => c.keywords))).map(keyword => ({
          value: keyword,
          text: keyword,
        })),
        isMatch: (contrib, selectedOptions) =>
          contrib.c.keywords.some(k => selectedOptions.includes(k)),
      },
    ],
    [contribList, contribsWithEditables]
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

  const filterableContribs = useMemo(
    () =>
      contribList.map(c => ({
        id: c.id,
        searchableId: c.friendlyId,
        searchableFields:
          c.editable && c.editable.editor
            ? [c.title, c.code, c.editable.editor.fullName]
            : [c.title, c.code],
        c,
      })),
    [contribList]
  );

  const handleFilterChange = filteredResults => {
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
    if (sortedList[index].editable) {
      return management ? (
        <a href={sortedList[index].editable.timelineURL}>{title}</a>
      ) : (
        <Link to={sortedList[index].editable.timelineURL}>{title}</Link>
      );
    }
    return <div>{title}</div>;
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

  const checkedEditablesRequest = async (urlFunc, data = {}, urlData = {}) => {
    let response;
    try {
      response = await indicoAxios.post(
        urlFunc({event_id: eventId, type: editableType, ...urlData}),
        {
          editables: checked,
          ...data,
        }
      );
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
    const rv = await checkedEditablesRequest(editablesArchiveURL, {}, {archive_type: 'archive'});
    if (rv) {
      location.href = rv.downloadURL;
    }
  };

  const exportJSON = async () => {
    setActiveRequest('json');
    const rv = await checkedEditablesRequest(editablesArchiveURL, {}, {archive_type: 'json'});
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
      {management && <ManagementPageSubTitle title={title} />}
      {management && (
        <ManagementPageBackButton url={editableTypeURL({event_id: eventId, type: editableType})} />
      )}
      <div styleName="editable-topbar">
        <div>
          {canAssignSelf && (
            <Button
              content={GetNextEditableTitles[editableType]}
              onClick={() => setSelfAssignModalVisible(true)}
            />
          )}
          {selfAssignModalVisible && (
            <NextEditable
              eventId={eventId}
              editableType={editableType}
              onClose={() => setSelfAssignModalVisible(false)}
              management={management}
            />
          )}
          {management && (
            <>
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
              <Button.Group>
                <Button
                  disabled={!hasCheckedContribs || !!activeRequest}
                  content={Translate.string('Download all files')}
                  onClick={downloadAllFiles}
                  loading={activeRequest === 'download'}
                />
                <Button
                  disabled={!hasCheckedContribs || !!activeRequest}
                  content={Translate.string('Export as JSON')}
                  onClick={exportJSON}
                  loading={activeRequest === 'json'}
                />
              </Button.Group>
            </>
          )}
        </div>
        <ListFilter
          list={filterableContribs}
          filterOptions={filterOptions}
          onChange={handleFilterChange}
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
                {management && (
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
                          checked.length ===
                            [...filteredSet].filter(x => contribIdSet.has(x)).length
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
                )}
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
      keywords: PropTypes.arrayOf(PropTypes.string).isRequired,
    })
  ).isRequired,
  editors: PropTypes.arrayOf(PropTypes.shape(userPropTypes)).isRequired,
  codePresent: PropTypes.bool.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
  eventId: PropTypes.number.isRequired,
  management: PropTypes.bool.isRequired,
  canAssignSelf: PropTypes.bool.isRequired,
};
