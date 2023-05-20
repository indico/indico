// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import deleteEditableURL from 'indico-url:event_editing.api_delete_editable';

import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Icon, Popup} from 'semantic-ui-react';

import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import {EditableType} from '../../models';

import * as selectors from './selectors';

export default function DeleteEditable() {
  const {eventId, contributionId, editableType} = useSelector(selectors.getStaticData);
  const allowed = useSelector(selectors.canDeleteEditable);
  const [submitting, setSubmitting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const title = {
    [EditableType.paper]: Translate.string('Delete paper'),
    [EditableType.slides]: Translate.string('Delete slide'),
    [EditableType.poster]: Translate.string('Delete poster'),
  }[editableType];

  if (!allowed) {
    return null;
  }

  const deleteEditable = async () => {
    setSubmitting(true);
    try {
      await indicoAxios.delete(
        deleteEditableURL({
          event_id: eventId,
          contrib_id: contributionId,
          type: editableType,
        })
      );
    } catch (error) {
      setSubmitting(false);
      return handleAxiosError(error);
    }
    setSubmitting(false);
  };

  return (
    <>
      <Popup
        content={title}
        trigger={
          <Icon
            name="trash"
            disabled={submitting}
            onClick={() => setIsOpen(true)}
            color="grey"
            link
          />
        }
      />
      <RequestConfirm
        header={title}
        confirmText={Translate.string('Delete')}
        onClose={() => setIsOpen(false)}
        requestFunc={deleteEditable}
        open={isOpen}
        negative
      >
        <Translate>This operation is not reversible. Are you sure you want to procceed?</Translate>
      </RequestConfirm>
    </>
  );
}
