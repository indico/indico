// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useSelector, useDispatch} from 'react-redux';
import {Icon, Modal, Popup, Segment} from 'semantic-ui-react';

import {RequestConfirmDelete} from 'indico/react/components';
import {Translate, Param} from 'indico/react/i18n';

import * as actions from './actions';
import {getDisabledSections} from './selectors';

import '../../styles/regform.module.scss';

function DisabledSection({id, title}) {
  const dispatch = useDispatch();
  const [confirmDeleteActive, setConfirmDeleteActive] = useState(false);

  const handleEnableClick = () => {
    dispatch(actions.enableSection(id));
  };

  const handleRemoveClick = () => {
    setConfirmDeleteActive(true);
  };

  return (
    <Segment>
      <span>{title}</span>
      <div styleName="actions">
        <Popup
          content={Translate.string('Restore')}
          trigger={
            <Icon
              name="undo"
              color="grey"
              size="small"
              onClick={handleEnableClick}
              circular
              inverted
            />
          }
        />
        <Popup
          content={Translate.string('Delete')}
          trigger={
            <Icon
              name="trash"
              color="red"
              size="small"
              onClick={handleRemoveClick}
              circular
              inverted
            />
          }
        />
      </div>
      <RequestConfirmDelete
        requestFunc={() => dispatch(actions.removeSection(id))}
        onClose={() => setConfirmDeleteActive(false)}
        open={confirmDeleteActive}
        size="mini"
        persistent
      >
        <Translate>
          Are you sure you want to delete the section "
          <Param name="field" value={title} wrapper={<strong />} />
          "?
        </Translate>
      </RequestConfirmDelete>
    </Segment>
  );
}

DisabledSection.propTypes = {
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
};

export default function DisabledSectionsModal({onClose}) {
  const sections = useSelector(getDisabledSections);

  useEffect(() => {
    // auto-close when there are no disabled sections left
    if (!sections.length) {
      onClose();
    }
  }, [onClose, sections.length]);

  return (
    <Modal open closeIcon size="mini" onClose={onClose}>
      <Modal.Header>
        <Translate>Disabled sections</Translate>
      </Modal.Header>
      <Modal.Content>
        <div styleName="disabled-sections">
          {sections.length
            ? sections.map(section => <DisabledSection key={section.id} {...section} />)
            : Translate.string('There are no disabled sections.')}
        </div>
      </Modal.Content>
    </Modal>
  );
}

DisabledSectionsModal.propTypes = {
  onClose: PropTypes.func.isRequired,
};
