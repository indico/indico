// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import reviewConditionsURL from 'indico-url:event_editing.api_review_conditions';

import React, {useState, useContext} from 'react';
import {Button, Divider, Loader, Message} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import ConditionInfo from './ConditionInfo';
import ReviewConditionsContext from './context';
import ReviewConditionForm from './ReviewConditionForm';

import './ReviewConditionsManager.module.scss';

export default function ReviewConditionsManager() {
  const {eventId, fileTypes, editableType} = useContext(ReviewConditionsContext);
  const [isAdding, setIsAdding] = useState(false);
  const {
    loading,
    reFetch,
    data: eventConditionsSetting,
    lastData,
  } = useIndicoAxios(reviewConditionsURL({event_id: eventId, type: editableType}));

  const eventConditions = eventConditionsSetting || lastData;
  if (loading && !lastData) {
    return <Loader inline="centered" active />;
  } else if (!eventConditions) {
    return null;
  }

  // map an array of ids to an array of file type objects
  const reviewConditions = eventConditions.map(([condId, condition]) => [
    condId,
    condition.map(fileTypeId => fileTypes.find(({id}) => id === fileTypeId)),
  ]);
  const createNewCondition = async formData => {
    try {
      await indicoAxios.post(
        reviewConditionsURL({event_id: eventId, type: editableType}),
        formData
      );
      setIsAdding(false);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  return (
    <div styleName="conditions-container">
      <Message info>
        <Translate>
          Here you can define what filetype-related conditions have to be met for a submission to be
          eligible for review. In order to start the review process, uploaded files must meet one of
          the specified criteria.
        </Translate>
      </Message>
      {eventConditions.length === 0 && (
        <Message info>
          <Translate>No reviewing conditions have been defined</Translate>
        </Message>
      )}
      <div>
        {reviewConditions.map(([condId, reviewCondition], index) => (
          <React.Fragment key={condId}>
            <div styleName="condition-row">
              <ConditionInfo
                fileTypes={reviewCondition}
                condId={condId}
                editableType={editableType}
                onUpdate={() => reFetch()}
                disableActions={loading}
              />
            </div>
            {index !== Object.keys(reviewConditions).length - 1 && (
              <Divider horizontal>
                <Translate>OR</Translate>
              </Divider>
            )}
          </React.Fragment>
        ))}
        {reviewConditions.length > 0 && (
          <Divider horizontal>
            <Translate>Or</Translate>
          </Divider>
        )}
        {isAdding ? (
          <div styleName="condition-row">
            <ReviewConditionForm
              onSubmit={createNewCondition}
              onDismiss={() => setIsAdding(false)}
            />
          </div>
        ) : (
          <Button
            onClick={() => setIsAdding(true)}
            disabled={isAdding || loading}
            floated="right"
            primary
          >
            <Translate>Create new filetype condition</Translate>
          </Button>
        )}
      </div>
    </div>
  );
}
