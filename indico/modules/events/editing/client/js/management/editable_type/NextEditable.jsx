// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import assignMyselfURL from 'indico-url:event_editing.api_assign_editable_self';
import fileTypesURL from 'indico-url:event_editing.api_file_types';
import editableListURL from 'indico-url:event_editing.api_filter_editables_by_filetypes';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState, useEffect, useMemo} from 'react';
import {useHistory} from 'react-router-dom';
import {Button, Loader, Modal, Table, Checkbox, Dimmer} from 'semantic-ui-react';

import {ListFilter} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import {fileTypePropTypes} from '../../editing/timeline/FileManager/util';
import {EditableType, GetNextEditableTitles} from '../../models';

import './NextEditable.module.scss';

export default function NextEditable({eventId, editableType, onClose, management}) {
  const {data: fileTypes, loading: isLoadingFileTypes} = useIndicoAxios({
    url: fileTypesURL({event_id: eventId, type: editableType}),
    camelize: true,
    trigger: [eventId, editableType],
  });

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
  const [filters, setFilters] = useState({});
  const [filteredEditables, setFilteredEditables] = useState(null);
  const [selectedEditable, setSelectedEditable] = useState(null);
  const [loading, setLoading] = useState(true);
  const history = useHistory();

  useEffect(() => {
    (async () => {
      setSelectedEditable(null);
      setLoading(true);
      let response;
      try {
        response = await indicoAxios.post(
          editableListURL({event_id: eventId, type: editableType}),
          {
            extensions: _.pickBy(filters, x => Array.isArray(x)),
            has_files: _.pickBy(filters, x => !Array.isArray(x)),
          }
        );
      } catch (e) {
        handleAxiosError(e);
        setLoading(false);
        return;
      }
      setFilteredEditables(camelizeKeys(response.data));
      setLoading(false);
    })();
  }, [eventId, editableType, filters]);

  const updatePresenceFilter = (id, present) => {
    if (filters[id] === present) {
      setFilters(_.omit(filters, id));
    } else {
      setFilters({...filters, [id]: present});
    }
  };

  const updateExtensionFilter = (id, extension) => {
    const typeFilter = filters[id];
    if (!Array.isArray(typeFilter)) {
      // switching from no filter or presence filter to extension filter
      setFilters({...filters, [id]: [extension]});
    } else if (!typeFilter.includes(extension)) {
      // adding previously-eselected extension
      setFilters({...filters, [id]: [...typeFilter, extension]});
    } else if (typeFilter.length === 1) {
      // deselecting last extension
      setFilters(_.omit(filters, id));
    } else {
      // deselecting some extension
      setFilters({...filters, [id]: _.without(typeFilter, extension)});
    }
  };

  const filterableEditables = useMemo(
    () =>
      filteredEditables?.map(e => ({
        id: e.id,
        searchableId: e.contributionFriendlyId,
        searchableFields: e.editor
          ? [e.contributionTitle, e.contributionCode, e.editor.fullName]
          : [e.contributionTitle, e.contributionCode],
        e,
      })),
    [filteredEditables]
  );

  const filterOptions = useMemo(
    () => [
      {
        key: 'code',
        text: Translate.string('Program code'),
        options: _.uniq(filteredEditables?.map(e => e.contributionCode).filter(x => x)).map(
          code => ({
            value: code,
            text: code,
          })
        ),
        isMatch: (editable, selectedOptions) =>
          selectedOptions.includes(editable.e.contributionCode),
      },
      {
        key: 'keywords',
        text: Translate.string('Keywords'),
        options: _.uniq(_.flatten(filteredEditables?.map(c => c.contributionKeywords))).map(
          keyword => ({
            value: keyword,
            text: keyword,
          })
        ),
        isMatch: (editable, selectedOptions) =>
          editable.e.contributionKeywords.some(k => selectedOptions.includes(k)),
      },
    ],
    [filteredEditables]
  );

  const handleFilterChange = filteredResults => {
    console.log(filteredResults);
    /* setFilteredSet(filteredResults);
    setSortedList(_sortList(sortBy, sortDirection, filteredResults));
    setChecked(
      contribsWithEditables
        .filter(row => checkedSet.has(row.editable.id) && filteredResults.has(row.id))
        .map(row => row.editable.id)
    ); */
  };

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
          {fileTypes.map(fileType => {
            return (
              <div key={fileType.id} styleName="filetype-list-item">
                <strong>{fileType.name}</strong>
                <div>
                  {fileType.extensions.length > 1 ? (
                    <>
                      <Button.Group size="small">
                        {fileType.extensions.map(extension => (
                          <Button
                            disabled={loading}
                            content={extension}
                            key={extension}
                            onClick={() => updateExtensionFilter(fileType.id, extension)}
                            color={
                              Array.isArray(filters[fileType.id]) &&
                              filters[fileType.id].includes(extension)
                                ? 'blue'
                                : null
                            }
                            toggle
                          />
                        ))}
                      </Button.Group>{' '}
                    </>
                  ) : (
                    <Button
                      disabled={loading}
                      size="small"
                      content={Translate.string('has files')}
                      color={filters[fileType.id] === true ? 'blue' : null}
                      onClick={() => updatePresenceFilter(fileType.id, true)}
                      toggle
                    />
                  )}
                  <Button
                    disabled={loading}
                    size="small"
                    content={Translate.string('has no files')}
                    color={filters[fileType.id] === false ? 'orange' : null}
                    onClick={() => updatePresenceFilter(fileType.id, false)}
                    toggle
                  />
                </div>
              </div>
            );
          })}
          <ListFilter
            list={filterableEditables}
            filterOptions={filterOptions}
            onChange={handleFilterChange}
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
    <Table basic="very" striped>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell style={{width: '2%'}} />
          <Table.HeaderCell style={{width: '6%'}}>ID</Table.HeaderCell>
          {codePresent && <Table.HeaderCell style={{width: '10%'}}>Code</Table.HeaderCell>}
          <Table.HeaderCell>Title</Table.HeaderCell>
          <Table.HeaderCell style={{width: '18%'}}>Editor</Table.HeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {filteredEditables.map(editable => (
          <Table.Row key={editable.id} style={editable.canAssignSelf ? {} : {opacity: '50%'}}>
            <Table.Cell>
              <Checkbox
                radio
                disabled={!editable.canAssignSelf}
                value={editable.id}
                checked={selectedEditable === editable}
                onChange={() => setSelectedEditable(editable)}
              />
            </Table.Cell>
            <Table.Cell>{editable.contributionFriendlyId}</Table.Cell>
            {codePresent && (
              <Table.Cell>
                {editable.contributionCode ? editable.contributionCode : Translate.string('n/a')}
              </Table.Cell>
            )}
            <Table.Cell>
              <a href={editable.timelineURL} target="_blank" rel="noopener noreferrer">
                {editable.contributionTitle}
              </a>
            </Table.Cell>
            <Table.Cell>{editable.editor ? editable.editor.fullName : ''}</Table.Cell>
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
