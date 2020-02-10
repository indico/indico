// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editReviewConditionURL from 'indico-url:event_editing.api_edit_review_condition';

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {useSelector} from 'react-redux';
import {Icon, Label} from 'semantic-ui-react';

import {RequestConfirm, TooltipIfTruncated} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {handleSubmitError} from 'indico/react/forms';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import ReviewConditionForm from './ReviewConditionForm';

import './ConditionInfo.module.scss';

export default function ConditionInfo({condition, uuid, onUpdate, disableActions}) {
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const {eventId} = useSelector(state => state.staticData);
  const url = editReviewConditionURL({confId: eventId, uuid});

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
      types={condition.map(cond => cond.id)}
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
        {condition.map((type, index) => (
          <React.Fragment key={type.id}>
            <TooltipIfTruncated>
              <Label basic>{type.name}</Label>
            </TooltipIfTruncated>
            {index !== condition.length - 1 && (
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
      <RequestConfirm
        header={Translate.string('Delete review condition')}
        confirmText={Translate.string('Yes')}
        cancelText={Translate.string('No')}
        onClose={() => setIsDeleting(false)}
        content={
          <div className="content">
            <Translate>Are you sure you want to delete this condition?</Translate>
          </div>
        }
        requestFunc={deleteCondition}
        open={isDeleting}
      />
    </>
  );
}

ConditionInfo.propTypes = {
  condition: PropTypes.array.isRequired,
  uuid: PropTypes.string.isRequired,
  onUpdate: PropTypes.func,
  disableActions: PropTypes.bool,
};

ConditionInfo.defaultProps = {
  onUpdate: null,
  disableActions: false,
};
