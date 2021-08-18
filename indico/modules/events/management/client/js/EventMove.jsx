// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventMoveURL from 'indico-url:event_management.move';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';

import {IButton} from 'indico/react/components';
import {FinalSubmitButton, FinalTextArea, handleSubmitError} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

export default function EventMove({eventId, currentCategoryId, hasPendingMoveRequest}) {
  const [targetCategory, setTargetCategory] = useState(null);

  const selectCategoryForMove = initialCategoryId => {
    $('<div>').categorynavigator({
      category: initialCategoryId,
      openInDialog: true,
      actionOn: {
        categoriesWithoutEventProposalOrCreationRights: {
          disabled: true,
        },
        categories: {
          disabled: true,
          ids: [currentCategoryId],
          message: Translate.string('The event is already in this category'),
        },
      },
      onAction(category) {
        setTargetCategory({
          id: category.id,
          path: category.path.map(x => x.title),
          moderated: !category.can_create_events,
        });
      },
    });
  };

  const closeModal = () => setTargetCategory(null);
  const changeCategory = () => {
    closeModal();
    selectCategoryForMove(targetCategory.id);
  };
  const submitMove = async ({comment}) => {
    const data = {target_category_id: targetCategory.id, comment};
    try {
      await indicoAxios.post(eventMoveURL({event_id: eventId}), data);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  return (
    <>
      <IButton
        borderless
        icon="transmission"
        title={Translate.string('Move event to another category')}
        disabled={hasPendingMoveRequest}
        onClick={() => selectCategoryForMove(currentCategoryId)}
      >
        <Translate>Move</Translate>
      </IButton>
      {targetCategory && (
        <FinalForm
          onSubmit={submitMove}
          initialValues={{comment: ''}}
          subscription={{submitting: true}}
        >
          {fprops => (
            <Modal
              open
              onClose={closeModal}
              size="tiny"
              dimmer="inverted"
              closeIcon={!fprops.submitting}
              closeOnEscape={!fprops.submitting}
              closeOnDimmerClick={!fprops.submitting}
            >
              <Modal.Header>
                <Translate>Confirm event move</Translate>
              </Modal.Header>
              <Modal.Content>
                <Form onSubmit={fprops.handleSubmit} id="move-event-form">
                  <Translate>
                    You are about to move this event to{' '}
                    <Param
                      name="target"
                      value={targetCategory.path.join(' » ')}
                      wrapper={<strong />}
                    />
                    .
                  </Translate>
                  {targetCategory.moderated && (
                    <>
                      <p>
                        <Translate>
                          Moving an event there{' '}
                          <Param name="strong" wrapper={<strong />}>
                            requires approval
                          </Param>{' '}
                          by a category manager. Until approved, the event will remain in its
                          current category.
                        </Translate>
                      </p>
                      <FinalTextArea
                        name="comment"
                        label={Translate.string('Comment')}
                        description={
                          <Translate>
                            You can provide a comment to the category managers to help them decide
                            whether to approve your move request.
                          </Translate>
                        }
                      />
                    </>
                  )}
                </Form>
              </Modal.Content>
              <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
                <FinalSubmitButton
                  label={Translate.string('Confirm')}
                  disabledUntilChange={false}
                  form="move-event-form"
                />
                <Button onClick={changeCategory} disabled={fprops.submitting}>
                  <Translate>Change category</Translate>
                </Button>
                <Button onClick={closeModal} disabled={fprops.submitting}>
                  <Translate>Cancel</Translate>
                </Button>
              </Modal.Actions>
            </Modal>
          )}
        </FinalForm>
      )}
    </>
  );
}

EventMove.propTypes = {
  eventId: PropTypes.number.isRequired,
  currentCategoryId: PropTypes.number.isRequired,
  hasPendingMoveRequest: PropTypes.bool.isRequired,
};
