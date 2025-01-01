// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import assignMyselfURL from 'indico-url:event_editing.api_assign_editable_self';
import fileTypesURL from 'indico-url:event_editing.api_file_types';
import editableListURL from 'indico-url:event_editing.api_filter_editables_by_filetypes';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState, useMemo, useRef} from 'react';
import {useHistory} from 'react-router-dom';
import {Button, Loader, Modal, Table, Checkbox, Dimmer, Icon} from 'semantic-ui-react';

import {ListFilter} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import {fileTypePropTypes} from '../../editing/timeline/FileManager/util';
import {EditableType, GetNextEditableTitles} from '../../models';

import './NextEditable.module.scss';

export default function NextEditable({eventId, editableType, onClose, management}) {
  const {data: fileTypes, loading: isLoadingFileTypes} = useIndicoAxios(
    fileTypesURL({event_id: eventId, type: editableType}),
    {camelize: true}
  );

  if (isLoadingFileTypes) {
    return <Loader active />;
  } else if (!fileTypes) {
    return null;
  }

  return (
    <NextEditableDisplay
      eventId={eventId}
      editableType={editableType}
      onClose={onClose}
      fileTypes={fileTypes}
      management={management}
    />
  );
}

NextEditable.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
  onClose: PropTypes.func.isRequired,
  management: PropTypes.bool.isRequired,
};

function NextEditableDisplay({eventId, editableType, onClose, fileTypes, management}) {
  const [editables, setEditables] = useState(null);
  const [filters, setFilters] = useState({});
  const [filteredSet, _setFilteredSet] = useState(new Set());
  const [selectedEditable, setSelectedEditable] = useState(null);
  const [loading, setLoading] = useState(true);
  const currFilters = useRef(null);
  const history = useHistory();

  const setFilteredSet = value => {
    _setFilteredSet(value);
    if (selectedEditable && !value.has(selectedEditable.id)) {
      setSelectedEditable(null);
    }
  };

  const getEditables = async _filters => {
    let response;
    try {
      response = await indicoAxios.post(editableListURL({event_id: eventId, type: editableType}), {
        extensions: _.pickBy(_filters, x => Array.isArray(x)),
        has_files: _.pickBy(_filters, x => !Array.isArray(x)),
      });
    } catch (e) {
      handleAxiosError(e);
      return;
    }
    return camelizeKeys(response.data);
  };

  const filterOptions = useMemo(
    () => [
      {
        key: 'session',
        text: Translate.string('Session'),
        options: _.uniqBy(editables?.map(e => e.contributionSession).filter(x => x), 'id').map(
          session => ({
            value: `${session.id}`,
            text: session.code ? `${session.code} - ${session.title}` : session.title,
          })
        ),
        isMatch: (editable, selectedOptions) =>
          editable.contributionSession &&
          selectedOptions.includes(`${editable.contributionSession.id}`),
      },
      {
        key: 'keywords',
        text: Translate.string('Keywords'),
        options: _.uniq(_.flatten(editables?.map(c => c.contributionKeywords))).map(keyword => ({
          value: keyword,
          text: keyword,
        })),
        isMatch: (editable, selectedOptions) =>
          editable.contributionKeywords.some(k => selectedOptions.includes(k)),
      },
      ...fileTypes.map(({id, name, extensions}) => ({
        key: `filetypes_${id}`,
        text: name,
        options: [
          ...(extensions.length > 1
            ? extensions.map(extension => ({value: `has_ext_${extension}`, text: extension}))
            : [{value: 'has_files', text: Translate.string('has files'), exclusive: true}]),
          {
            value: 'has_no_files',
            text: Translate.string('has no files'),
            exclusive: true,
          },
        ],
      })),
    ],
    [editables, fileTypes]
  );

  const onChangeFilters = async activeFilters => {
    const filetypesKeyExpr = /^filetypes_(\d+)$/;
    const formatFilterOptions = options => {
      const extOptionExpr = /^has_ext_(.*)$/;
      const extensionOptions = Object.keys(options).filter(o => extOptionExpr.exec(o));
      return extensionOptions.length > 0
        ? extensionOptions.map(o => extOptionExpr.exec(o)[1])
        : !options.has_no_files;
    };
    const newFilters = Object.keys(activeFilters)
      .filter(f => filetypesKeyExpr.exec(f))
      .reduce(
        (acc, f) => ({
          ...acc,
          [+filetypesKeyExpr.exec(f)[1]]: formatFilterOptions(activeFilters[f]),
        }),
        {}
      );
    let _editables = editables;
    if (!_.isEqual(currFilters.current, newFilters)) {
      setLoading(true);
      _editables = await getEditables(newFilters);
      setLoading(false);
      setEditables(_editables);
      currFilters.current = newFilters;
    }
    const filtered = _editables.filter(x =>
      filterOptions.every(
        ({key, isMatch}) =>
          !activeFilters[key] || !isMatch || isMatch(x, Object.keys(activeFilters[key] || {}))
      )
    );
    setFilters(activeFilters);
    setFilteredSet(new Set(filtered.map(e => e.id)));
  };

  const filteredEditables = useMemo(
    () =>
      _.orderBy(
        editables?.map(e => ({
          ...e,
          canAssignSelf: filteredSet.has(e.id) ? e.canAssignSelf : false,
        })) || [],
        'canAssignSelf',
        'desc'
      ),
    [editables, filteredSet]
  );

  const handleAssign = async () => {
    try {
      await indicoAxios.put(
        assignMyselfURL({
          event_id: eventId,
          contrib_id: selectedEditable.contributionId,
          type: editableType,
        })
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    if (management) {
      location.href = selectedEditable.timelineURL;
    } else {
      history.push(selectedEditable.timelineURL);
    }
  };

  return (
    <Modal onClose={onClose} closeOnDimmerClick={false} open>
      <Modal.Header>{GetNextEditableTitles[editableType]}</Modal.Header>
      <Modal.Content>
        <div styleName="filetype-list">
          <ListFilter
            name={`get-next-${editableType}-filter-${eventId}`}
            list={editables || []}
            filters={filters}
            filterOptions={filterOptions}
            searchableId={e => e.contributionFriendlyId}
            searchableFields={e => [
              e.contributionTitle,
              e.contributionCode,
              ...e.contributionPersons,
            ]}
            onChangeFilters={onChangeFilters}
            onChangeList={setFilteredSet}
          />
        </div>
        <Dimmer.Dimmable styleName="filtered-editables" dimmed={loading}>
          <NextEditableTable
            filteredEditables={filteredEditables}
            selectedEditable={selectedEditable}
            setSelectedEditable={setSelectedEditable}
          />
          <Dimmer active={loading} inverted>
            <Loader />
          </Dimmer>
        </Dimmer.Dimmable>
      </Modal.Content>
      <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
        <Button onClick={onClose}>
          <Translate>Cancel</Translate>
        </Button>
        <Button color="blue" onClick={handleAssign} disabled={selectedEditable === null}>
          <Translate>Assign to myself</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

NextEditableDisplay.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  management: PropTypes.bool.isRequired,
};

function NextEditableTable({filteredEditables, selectedEditable, setSelectedEditable}) {
  if (filteredEditables === null) {
    return null;
  }

  const codePresent = Object.values(filteredEditables).some(c => c.contributionCode);

  return filteredEditables.length ? (
    <Table basic="very" striped selectable>
      <Table.Body>
        {filteredEditables.map(editable => (
          <Table.Row
            key={editable.id}
            style={editable.canAssignSelf ? {} : {opacity: '50%'}}
            styleName="editable"
            onClick={() => setSelectedEditable(editable)}
            active={selectedEditable?.id === editable.id}
          >
            <Table.Cell width={1}>
              <Checkbox
                radio
                disabled={!editable.canAssignSelf}
                value={editable.id}
                checked={selectedEditable?.id === editable.id}
                onChange={() => setSelectedEditable(editable)}
              />
            </Table.Cell>
            <Table.Cell width={1}>{editable.contributionFriendlyId}</Table.Cell>
            {codePresent && (
              <Table.Cell width={2}>
                {editable.contributionCode ? editable.contributionCode : Translate.string('n/a')}
              </Table.Cell>
            )}
            <Table.Cell>{editable.contributionTitle}</Table.Cell>
            <Table.Cell width={1}>
              <a href={editable.timelineURL} target="_blank" rel="noopener noreferrer">
                <Icon name="eye" />
              </a>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  ) : (
    <div styleName="no-editables-available">
      <Translate>There are no editables available.</Translate>
    </div>
  );
}

NextEditableTable.propTypes = {
  filteredEditables: PropTypes.array,
  selectedEditable: PropTypes.object,
  setSelectedEditable: PropTypes.func.isRequired,
};

NextEditableTable.defaultProps = {
  filteredEditables: null,
  selectedEditable: null,
};
