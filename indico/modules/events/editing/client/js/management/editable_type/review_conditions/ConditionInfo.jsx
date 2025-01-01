// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editReviewConditionURL from 'indico-url:event_editing.api_edit_review_condition';

import PropTypes from 'prop-types';
import React, {useState, useContext} from 'react';
import {Icon, Label} from 'semantic-ui-react';

import {RequestConfirmDelete, TooltipIfTruncated} from 'indico/react/components';
import {handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import {EditableType} from '../../../models';

import ReviewConditionsContext from './context';
import ReviewConditionForm from './ReviewConditionForm';

import './ConditionInfo.module.scss';

export default function ConditionInfo({fileTypes, condId, editableType, onUpdate, disableActions}) {
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const {eventId} = useContext(ReviewConditionsContext);
  const url = editReviewConditionURL({event_id: eventId, condition_id: condId, type: editableType});

  const deleteCondition = async () => {
    try {
      await indicoAxios.delete(url);
    } catch (e) {
      handleAxiosError(e);
      return true;
    }

    if (onUpdate) {
      onUpdate();
    }
  };

  return isEditing ? (
    <ReviewConditionForm
      types={fileTypes.map(ft => ft.id)}
      onDismiss={() => setIsEditing(false)}
      onSubmit={async formData => {
        try {
          await indicoAxios.patch(url, formData);
        } catch (e) {
          return handleSubmitError(e);
        }

        if (onUpdate) {
          onUpdate();
        }
        setIsEditing(false);
      }}
    />
  ) : (
    <>
      <div styleName="types-list">
        {fileTypes.map((type, index) => (
          <React.Fragment key={type.id}>
            <TooltipIfTruncated>
              <Label basic>{type.name}</Label>
            </TooltipIfTruncated>
            {index !== fileTypes.length - 1 && (
              <Label as="span" color="orange" size="small" circular>
                <Translate>AND</Translate>
              </Label>
            )}
          </React.Fragment>
        ))}
      </div>
      <div styleName="condition-actions">
        <Icon
          color="blue"
          name="pencil"
          onClick={() => setIsEditing(true)}
          disabled={disableActions}
        />
        <Icon
          color="red"
          name="trash"
          onClick={() => setIsDeleting(true)}
          disabled={disableActions}
        />
      </div>
      <RequestConfirmDelete
        onClose={() => setIsDeleting(false)}
        requestFunc={deleteCondition}
        open={isDeleting}
      >
        <Translate>Are you sure you want to delete this condition?</Translate>
      </RequestConfirmDelete>
    </>
  );
}

ConditionInfo.propTypes = {
  fileTypes: PropTypes.array.isRequired,
  condId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
  onUpdate: PropTypes.func,
  disableActions: PropTypes.bool,
};

ConditionInfo.defaultProps = {
  onUpdate: null,
  disableActions: false,
};
