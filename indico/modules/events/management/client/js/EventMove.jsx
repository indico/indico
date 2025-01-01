// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import bulkEventMoveURL from 'indico-url:categories.move_events';
import eventMoveURL from 'indico-url:event_management.move';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';

import {IButton} from 'indico/react/components';
import {FinalSubmitButton, FinalTextArea, handleSubmitError} from 'indico/react/forms';
import {Param, Translate, PluralTranslate, Singular, Plural} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

function EventMove({currentCategoryId, submitMove, renderTrigger, getEventCount, bulk, publish}) {
  const [targetCategory, setTargetCategory] = useState(null);

  const selectCategoryForMove = initialCategoryId => {
    let dialogTitle;
    if (publish) {
      dialogTitle = Translate.string('Publish event');
    } else if (bulk) {
      dialogTitle = Translate.string('Move events');
    } else {
      dialogTitle = Translate.string('Move event');
    }

    $('<div>').categorynavigator({
      category: initialCategoryId,
      openInDialog: true,
      dialogTitle,
      dialogSubtitle: bulk
        ? Translate.string('Select destination category for the selected events')
        : Translate.string('Select destination category for the event'),
      actionOn: {
        categoriesWithoutEventProposalOrCreationRights: {
          disabled: true,
        },
        categories: {
          disabled: true,
          ids: currentCategoryId ? [currentCategoryId] : [],
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

  const eventCount = bulk ? getEventCount() : 1;
  const closeModal = () => setTargetCategory(null);
  const changeCategory = () => {
    closeModal();
    selectCategoryForMove(targetCategory.id);
  };

  return (
    <>
      {renderTrigger(() => selectCategoryForMove(currentCategoryId))}
      {targetCategory && (
        <FinalForm
          onSubmit={data => submitMove(targetCategory.id, data)}
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
                  {publish ? (
                    <Translate>
                      You are about to publish this event to{' '}
                      <Param
                        name="target"
                        value={targetCategory.path.join(' » ')}
                        wrapper={<strong />}
                      />
                      .
                    </Translate>
                  ) : (
                    <PluralTranslate count={eventCount}>
                      <Singular>
                        You are about to move this event to{' '}
                        <Param
                          name="target"
                          value={targetCategory.path.join(' » ')}
                          wrapper={<strong />}
                        />
                        .
                      </Singular>
                      <Plural>
                        You are about to move <Param name="count" value={eventCount} /> events to{' '}
                        <Param
                          name="target"
                          value={targetCategory.path.join(' » ')}
                          wrapper={<strong />}
                        />
                        .
                      </Plural>
                    </PluralTranslate>
                  )}
                  {targetCategory.moderated && (
                    <>
                      <p>
                        {publish ? (
                          <>
                            Publishing an event there{' '}
                            <Param name="strong" wrapper={<strong />}>
                              requires approval
                            </Param>{' '}
                            by a category manager. Until approved, the event will remain unlisted.
                          </>
                        ) : (
                          <PluralTranslate count={eventCount}>
                            <Singular>
                              Moving an event there{' '}
                              <Param name="strong" wrapper={<strong />}>
                                requires approval
                              </Param>{' '}
                              by a category manager. Until approved, the event will remain in its
                              current category.
                            </Singular>
                            <Plural>
                              Moving events there{' '}
                              <Param name="strong" wrapper={<strong />}>
                                requires approval
                              </Param>{' '}
                              by a category manager. Until approved, the events will remain in their
                              current category.
                            </Plural>
                          </PluralTranslate>
                        )}
                      </p>
                      <FinalTextArea
                        name="comment"
                        label={Translate.string('Comment')}
                        description={
                          <Translate>
                            You can provide a comment to the category managers to help them decide
                            whether to approve your request.
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
  bulk: PropTypes.bool,
  submitMove: PropTypes.func.isRequired,
  renderTrigger: PropTypes.func.isRequired,
  getEventCount: PropTypes.func,
  currentCategoryId: PropTypes.number,
  publish: PropTypes.bool,
};

EventMove.defaultProps = {
  bulk: false,
  currentCategoryId: null,
  getEventCount: null,
  publish: false,
};

export function SingleEventMove({
  eventId,
  currentCategoryId,
  hasPendingMoveRequest,
  inCategoryManagement,
}) {
  const submitMove = async (targetCategoryId, {comment}) => {
    const data = {target_category_id: targetCategoryId, comment};
    try {
      await indicoAxios.post(eventMoveURL({event_id: eventId}), data);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const renderTrigger = inCategoryManagement
    ? fn => (
        <a
          className={`i-link icon-transmission ${hasPendingMoveRequest ? 'disabled' : ''}`}
          title={
            hasPendingMoveRequest
              ? Translate.string('Event has a pending move request')
              : Translate.string('Move event to another category')
          }
          onClick={!hasPendingMoveRequest ? fn : undefined}
        />
      )
    : fn => (
        <IButton
          borderless
          icon="transmission"
          title={Translate.string('Move event to another category')}
          disabled={hasPendingMoveRequest}
          onClick={fn}
        >
          <Translate>Move</Translate>
        </IButton>
      );

  return (
    <EventMove
      submitMove={submitMove}
      renderTrigger={renderTrigger}
      currentCategoryId={currentCategoryId}
    />
  );
}

SingleEventMove.propTypes = {
  eventId: PropTypes.number.isRequired,
  currentCategoryId: PropTypes.number.isRequired,
  hasPendingMoveRequest: PropTypes.bool.isRequired,
  inCategoryManagement: PropTypes.bool,
};

SingleEventMove.defaultProps = {
  inCategoryManagement: false,
};

export function BulkEventMove({currentCategoryId, getEventData}) {
  const submitMove = async (targetCategoryId, {comment}) => {
    const selectedEventData = getEventData();
    const data = {
      target_category_id: targetCategoryId,
      all_selected: selectedEventData.allSelected,
      event_id: selectedEventData.allSelected ? [] : selectedEventData.eventIds,
      comment,
    };
    try {
      await indicoAxios.post(bulkEventMoveURL({category_id: currentCategoryId}), data);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const renderTrigger = fn => (
    <IButton
      href="#"
      icon="transmission"
      classes={{'js-enabled-if-checked': true}}
      title={Translate.string('Move selected events to another category')}
      onClick={fn}
    />
  );

  return (
    <EventMove
      submitMove={submitMove}
      renderTrigger={renderTrigger}
      currentCategoryId={currentCategoryId}
      getEventCount={() => getEventData().eventCount}
      bulk
    />
  );
}

BulkEventMove.propTypes = {
  currentCategoryId: PropTypes.number.isRequired,
  getEventData: PropTypes.func.isRequired,
};

export function EventPublish({eventId, hasPendingPublishRequest}) {
  const submitMove = async (targetCategoryId, {comment}) => {
    const data = {target_category_id: targetCategoryId, comment};
    try {
      await indicoAxios.post(eventMoveURL({event_id: eventId}), data);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const renderTrigger = fn => (
    <IButton
      highlight
      icon="play"
      title={
        hasPendingPublishRequest
          ? Translate.string('Event has a pending publish request')
          : Translate.string('Publish event to a category')
      }
      disabled={hasPendingPublishRequest}
      onClick={fn}
    >
      <Translate>Publish</Translate>
    </IButton>
  );

  return <EventMove submitMove={submitMove} renderTrigger={renderTrigger} publish />;
}

EventPublish.propTypes = {
  eventId: PropTypes.number.isRequired,
  hasPendingPublishRequest: PropTypes.bool.isRequired,
};
