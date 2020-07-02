// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableListURL from 'indico-url:event_editing.api_filter_editables_by_filetypes';
import assignMyselfURL from 'indico-url:event_editing.api_assign_editable_self';
import fileTypesURL from 'indico-url:event_editing.api_file_types';

import _ from 'lodash';
import React, {useState, useEffect} from 'react';
import PropTypes from 'prop-types';
import {Button, Loader, Modal, Table, Checkbox, Dimmer} from 'semantic-ui-react';
import {camelizeKeys} from 'indico/utils/case';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {useIndicoAxios} from 'indico/react/hooks';
import {EditableType} from '../../models';
import {fileTypePropTypes} from '../../editing/timeline/FileManager/util';

import './NextEditable.module.scss';

export default function NextEditable({eventId, editableType, onClose}) {
  const {data: fileTypes, loading: isLoadingFileTypes} = useIndicoAxios({
    url: fileTypesURL({confId: eventId, type: editableType}),
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
    />
  );
}

NextEditable.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
  onClose: PropTypes.func.isRequired,
};

function NextEditableDisplay({eventId, editableType, onClose, fileTypes}) {
  const [filters, setFilters] = useState({});
  const [filteredEditables, setFilteredEditables] = useState(null);
  const [selectedEditable, setSelectedEditable] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setSelectedEditable(null);
      setLoading(true);
      let response;
      try {
        response = await indicoAxios.post(editableListURL({confId: eventId, type: editableType}), {
          extensions: _.pickBy(filters, x => Array.isArray(x)),
          has_files: _.pickBy(filters, x => !Array.isArray(x)),
        });
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

  const handleAssign = async () => {
    try {
      await indicoAxios.put(
        assignMyselfURL({
          confId: eventId,
          contrib_id: selectedEditable.contributionId,
          type: editableType,
        })
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    location.href = selectedEditable.timelineURL;
  };

  const titleByType = {
    paper: Translate.string('Get next paper'),
    poster: Translate.string('Get next poster'),
    slides: Translate.string('Get next slides'),
  };

  return (
    <Modal onClose={onClose} closeOnDimmerClick={false} open>
      <Modal.Header>{titleByType[editableType]}</Modal.Header>
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
          <Table.Row key={editable.id}>
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
