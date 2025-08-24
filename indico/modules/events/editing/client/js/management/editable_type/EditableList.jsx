// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import applyJudgmentURL from 'indico-url:event_editing.api_apply_judgment';
import assignEditorURL from 'indico-url:event_editing.api_assign_editor';
import assignSelfEditorURL from 'indico-url:event_editing.api_assign_myself';
import createCommentURL from 'indico-url:event_editing.api_create_comment';
import editableListURL from 'indico-url:event_editing.api_editable_list';
import editorsURL from 'indico-url:event_editing.api_editable_type_editors';
import canAssignSelfURL from 'indico-url:event_editing.api_editor_self_assign_allowed';
import editablesArchiveURL from 'indico-url:event_editing.api_prepare_editables_archive';
import unassignEditorURL from 'indico-url:event_editing.api_unassign_editor';
import editableTypeURL from 'indico-url:event_editing.manage_editable_type';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState, useMemo, useEffect} from 'react';
import {useParams, Link} from 'react-router-dom';
import {Column, Table, SortDirection, WindowScroller} from 'react-virtualized';
import {Button, Icon, Loader, Checkbox, Message, Dropdown, Confirm, Popup} from 'semantic-ui-react';

import {
  TooltipIfTruncated,
  ManagementPageSubTitle,
  ManagementPageBackButton,
  ListFilter,
} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import Palette from 'indico/utils/palette';
import {natSortCompare} from 'indico/utils/sort';

import StateIndicator from '../../editing/timeline/StateIndicator';
import {userPropTypes} from '../../editing/timeline/util';
import {EditableType, GetNextEditableTitles} from '../../models';

import CommentButton from './CommentButton';
import NextEditable from './NextEditable';

import './EditableList.module.scss';

export default function EditableList({management}) {
  const eventId = useNumericParam('event_id');
  const {type} = useParams();
  const {data: contribList, loading: isLoadingContribList} = useIndicoAxios(
    editableListURL({event_id: eventId, type}),
    {camelize: true}
  );
  const {data: editors, loading: isLoadingEditors} = useIndicoAxios(
    editorsURL({event_id: eventId, type}),
    {camelize: true, manual: !management}
  );
  const {data: canAssignSelf, loading: isLoadingCanAssignSelf} = useIndicoAxios(
    canAssignSelfURL({event_id: eventId, type}),
    {manual: management}
  );

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

const processContribList = contribList =>
  contribList.map(c => {
    const lastUpdate = c.editable && localStorage.getItem(`editable-${c.editable.id}-last-update`);
    return {
      ...c,
      hasUpdates: lastUpdate && c.editable.lastUpdateDt !== lastUpdate,
    };
  });

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

  const [contribList, setContribList] = useState(processContribList(initialContribList));
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
  const editorAssignments = Object.fromEntries(
    checkedContribsWithEditables
      .filter(x => x.editable.editor)
      .map(x => [x.editable.id, x.editable.editor.identifier])
  );
  const [activeRequest, setActiveRequest] = useState(null);
  const [assignmentConflict, setAssignmentConflict] = useState(null);
  const [skippedEditables, setSkippedEditables] = useState(0);

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

  const judgmentOptions = [
    {
      key: 'accept',
      value: 'accept',
      text: Translate.string('Accept'),
      label: {color: 'green', empty: true, circular: true},
    },
    {
      key: 'reject',
      value: 'reject',
      text: Translate.string('Reject'),
      label: {color: 'black', empty: true, circular: true},
    },
  ];

  const filterOptions = useMemo(
    () => [
      {
        key: 'state',
        text: Translate.string('Status'),
        options: [
          {
            value: 'not_submitted',
            text: Translate.string('Not submitted', 'Editable'),
            color: 'default',
          },
          {
            value: 'ready_for_review',
            text: Translate.string('Ready for review', 'Editable'),
            color: 'grey',
          },
          {
            value: 'accepted',
            text: Translate.string('Accepted', 'Editable'),
            exclusive: true,
            color: 'green',
          },
          {
            value: 'accepted_submitter',
            text: Translate.string('Accepted by Submitter', 'Editable'),
            exclusive: true,
            color: 'olive',
          },
          {
            value: 'rejected',
            text: Translate.string('Rejected', 'Editable'),
            exclusive: true,
            color: 'black',
          },
          {
            value: 'needs_submitter_changes',
            text: Translate.string('Needs submitter changes', 'Editable'),
            exclusive: true,
            color: 'red',
          },
          {
            value: 'needs_submitter_confirmation',
            text: Translate.string('Needs submitter confirmation', 'Editable'),
            exclusive: true,
            color: 'yellow',
          },
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
        key: 'session',
        text: Translate.string('Session'),
        options: _.uniqBy(
          contribList.map(c => c.session).filter(x => x),
          'id'
        ).map(session => ({
          value: `${session.id}`,
          text: session.code ? `${session.code} - ${session.title}` : session.title,
        })),
        isMatch: (contrib, selectedOptions) =>
          contrib.c.session && selectedOptions.includes(`${contrib.c.session.id}`),
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
      {
        key: 'tags',
        text: Translate.string('Tags'),
        options: _.uniqBy(
          contribsWithEditables
            .map(c => c.editable.tags)
            .filter(x => x.length)
            .reduce((pre, cur) => pre.concat(cur), []),
          'code'
        ).map(t => ({value: t.code, text: t.code, color: t.color})),
        isMatch: (contrib, selectedOptions) =>
          contrib.c.editable?.tags &&
          selectedOptions.some(tag => contrib.c.editable.tags.map(t => t.code).includes(tag)),
      },
      {
        key: 'has_updates',
        text: Translate.string('Has updates'),
        options: [
          {value: 'true', text: Translate.string('Yes'), exclusive: true},
          {value: 'false', text: Translate.string('No'), exclusive: true},
        ],
        isMatch: (contrib, selectedOptions) =>
          (selectedOptions.includes('true') && contrib.c.hasUpdates) ||
          (selectedOptions.includes('false') && !contrib.c.hasUpdates),
      },
    ],
    [contribList, contribsWithEditables]
  );

  const title = {
    [EditableType.paper]: Translate.string('List of papers'),
    [EditableType.slides]: Translate.string('List of slides'),
    [EditableType.poster]: Translate.string('List of posters'),
  }[editableType];

  const skippedEditablesWarning = {
    [EditableType.paper]: PluralTranslate.string(
      '{count} paper was skipped because of its current status.',
      '{count} papers were skipped because of their current status.',
      skippedEditables,
      {count: skippedEditables}
    ),
    [EditableType.slides]: PluralTranslate.string(
      '{count} slide was skipped because of its current status.',
      '{count} slides were skipped because of their current status.',
      skippedEditables,
      {count: skippedEditables}
    ),
    [EditableType.poster]: PluralTranslate.string(
      '{count} poster was skipped because of its current status.',
      '{count} posters were skipped because of their current status.',
      skippedEditables,
      {count: skippedEditables}
    ),
  }[editableType];

  const columnHeaders = [
    ['friendlyId', Translate.string('ID'), 60],
    ...(codePresent ? [['code', Translate.string('Code'), 110]] : []),
    ['title', Translate.string('Title'), 600],
    ['revision', Translate.string('Rev.'), 80],
    ['status', Translate.string('Status'), 200],
    ['editor', Translate.string('Editor'), 400],
  ];

  const programCodeKey = contribution => contribution.code;
  const titleKey = contribution => contribution.title.toLowerCase();
  const revisionKey = contribution => contribution.editable && contribution.editable.revisionCount;
  const statusKey = contribution =>
    contribution.editable && contribution.editable.state.toLowerCase();
  const editorKey = contribution =>
    contribution.editable &&
    contribution.editable.editor &&
    contribution.editable.editor.fullName.toLowerCase();

  const sortKeys = {
    code: programCodeKey,
    title: titleKey,
    revision: revisionKey,
    status: statusKey,
    editor: editorKey,
  };

  const sortFuncs = {
    code: (arr, key) => [...arr].sort((a, b) => natSortCompare(key(a), key(b))),
  };

  // eslint-disable-next-line no-shadow
  const _sortList = (sortBy, sortDirection, filteredResults) => {
    const sortKey = sortKeys[sortBy] || (x => x[sortBy]);
    const sortFn = sortFuncs[sortBy] || ((arr, key) => _.sortBy(arr, key));
    const newList = sortFn(contribList, sortKey);
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
    updatedEditables.forEach(e => {
      localStorage.setItem(`editable-${e.id}-last-update`, e.lastUpdateDt);
    });
    updatedEditables = new Map(updatedEditables.map(x => [x.id, x]));
    const _mapper = contrib => {
      if (!contrib.editable || !updatedEditables.has(contrib.editable.id)) {
        return contrib;
      }
      return {...contrib, editable: updatedEditables.get(contrib.editable.id)};
    };
    setContribList(list => processContribList(list.map(_mapper)));
    setSortedList(list => processContribList(list.map(_mapper)));
  };

  const filterableContribs = useMemo(
    () =>
      contribList.map(c => ({
        id: c.id,
        searchableId: c.friendlyId,
        searchableFields:
          c.editable && c.editable.editor
            ? [c.title, c.code, ...c.persons, c.editable.editor.fullName]
            : [c.title, c.code, ...c.persons],
        c,
      })),
    [contribList]
  );

  const onChangeList = filteredResults => {
    setFilteredSet(filteredResults);
    setSortedList(_sortList(sortBy, sortDirection, filteredResults));
    setChecked(
      contribsWithEditables
        .filter(row => checkedSet.has(row.editable.id) && filteredResults.has(row.id))
        .map(row => row.editable.id)
    );
  };

  const renderId = (id, __, rowIndex) => {
    if (sortedList[rowIndex].hasUpdates) {
      return (
        <Popup
          trigger={
            <div styleName="id-cell">
              <Icon size="mini" color="red" name="circle" />
              {id}
            </div>
          }
          content={Translate.string('There has been an update to the latest revision')}
        />
      );
    }
    return id;
  };
  const renderCode = code => code || Translate.string('n/a');
  const renderEditor = (__, editable) => {
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
  const renderTitle = (title, __, index) => {
    if (sortedList[index].editable) {
      return management ? (
        <a href={sortedList[index].editable.timelineURL}>{title}</a>
      ) : (
        <Link to={sortedList[index].editable.timelineURL}>{title}</Link>
      );
    }
    return <div>{title}</div>;
  };
  const renderStatus = (__, editable, rowIndex) => {
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
    friendlyId: renderId,
    title: renderTitle,
    code: renderCode,
    revision: editable => (editable ? editable.revisionCount : ''),
    status: renderStatus,
    editor: renderEditor,
  };

  // eslint-disable-next-line react/prop-types
  const renderCell = ({dataKey, rowIndex}) => {
    const row = sortedList[rowIndex];
    const fn = renderFuncs[dataKey];
    return (
      <TooltipIfTruncated>
        <div
          styleName="rowcolumn-tooltip"
          role="gridcell"
          style={dataKey === 'title' ? {display: 'block'} : {}}
        >
          {fn(row[dataKey], row.editable, rowIndex)}
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
      setActiveRequest(null);
    } catch (error) {
      if (error.response?.status === 409 && error.response.data.editor_conflict) {
        setAssignmentConflict([urlFunc, {...data, force: true}]);
        return null;
      }
      handleAxiosError(error);
      setActiveRequest(null);
      return null;
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
    return rv;
  };

  const checkedEditablesAssignmentRequest = async (type, urlFunc, data = {}) =>
    updateCheckedEditablesRequest(type, urlFunc, {
      ...data,
      editor_assignments: editorAssignments,
    });

  const assignEditor = editor => {
    checkedEditablesAssignmentRequest('assign', assignEditorURL, {editor});
  };

  const assignSelfEditor = () => {
    checkedEditablesAssignmentRequest('assign-self', assignSelfEditorURL);
  };

  const unassignEditor = async () => {
    checkedEditablesAssignmentRequest('unassign', unassignEditorURL);
  };

  const createComment = data => {
    setActiveRequest('comment');
    checkedEditablesRequest(createCommentURL, data);
  };

  const applyJudgment = async action => {
    const rv = await updateCheckedEditablesRequest('judgment', applyJudgmentURL, {action});
    if (rv) {
      setSkippedEditables(checked.length - rv.length);
    }
  };

  // make the page full-width
  useEffect(() => {
    document.body.classList.add('full-width-content-wrapper');
    return () => {
      document.body.classList.remove('full-width-content-wrapper');
    };
  }, []);

  return (
    <>
      {management && <ManagementPageSubTitle title={title} />}
      {management && (
        <ManagementPageBackButton url={editableTypeURL({event_id: eventId, type: editableType})} />
      )}
      <div styleName="editable-topbar">
        <div styleName="editable-actions">
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
                  content={Translate.string('Unassign', 'Editable')}
                  onClick={unassignEditor}
                  loading={activeRequest === 'unassign'}
                />
              </Button.Group>
              <CommentButton
                disabled={!hasCheckedContribs || !!activeRequest}
                onSubmit={createComment}
                loading={activeRequest === 'comment'}
              />
              <Dropdown
                disabled={!hasCheckedContribs || !!activeRequest}
                options={judgmentOptions}
                scrolling
                icon={null}
                value={null}
                selectOnBlur={false}
                selectOnNavigation={false}
                onChange={(evt, {value}) => applyJudgment(value)}
                trigger={
                  <Button icon loading={activeRequest === 'judgment'}>
                    <Translate>Judge</Translate>
                    <Icon name="caret down" />
                  </Button>
                }
              />
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
          name={`${editableType}-list-filter-${eventId}`}
          list={filterableContribs || []}
          filterOptions={filterOptions}
          searchableId={e => e.searchableId}
          searchableFields={e => e.searchableFields}
          onChangeList={onChangeList}
        />
      </div>
      {!!skippedEditables && (
        <Message warning>
          <Icon name="warning sign" />
          {skippedEditablesWarning}
        </Message>
      )}
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
      <Confirm
        open={!!assignmentConflict}
        header={Translate.string('Assignment conflict')}
        content={Translate.string(
          'Some editor assignments for the current selection have been changed externally. Are you sure you want to proceed?'
        )}
        confirmButton={<Button content={Translate.string('Force assignments')} negative />}
        cancelButton={Translate.string('Cancel')}
        onCancel={() => {
          setActiveRequest(null);
          setAssignmentConflict(null);
        }}
        onConfirm={() => {
          updateCheckedEditablesRequest(activeRequest, ...assignmentConflict);
          setAssignmentConflict(null);
        }}
      />
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
