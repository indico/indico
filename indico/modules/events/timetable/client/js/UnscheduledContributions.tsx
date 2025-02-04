// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Field, Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Form, Icon} from 'semantic-ui-react';

import {CollapsibleContainer} from 'indico/react/components';
import {FinalInput, FinalSubmitButton} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';

import * as actions from './actions';
import {useDraggable} from './dnd';
import {ContributionDetails} from './EntryDetails';
import * as selectors from './selectors';
import {entrySchema, entryTypes, formatTitle} from './util';

import './UnscheduledContributions.module.scss';

function DraggableUnscheduledContribution({id, children}: {id: number; children: React.ReactNode}) {
  const draggableId = `unscheduled-${id}`;
  const {attributes, listeners, setNodeRef, transform, isDragging} = useDraggable({
    id: draggableId,
  });

  const style: Record<string, string | number | undefined> = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        position: 'relative',
        zIndex: 900,
        cursor: isDragging ? 'grabbing' : 'grab',
      }
    : {};

  return (
    <div style={style} ref={setNodeRef} {...listeners} {...attributes}>
      {children}
    </div>
  );
}

function UnscheduledContributionList({
  contribs,
  uses24HourFormat,
  dispatch,
  selected,
  setSelected,
  showSession,
}) {
  const sessions = useSelector(selectors.getSessions);

  const makeHandleSelect = id => e => {
    e.stopPropagation();
    const set = new Set([...selected, id]);
    if (selected.has(id)) {
      set.delete(id);
    }
    setSelected(set);
  };

  const makeHandleDrag = id => () => {
    if (selected.has(id)) {
      dispatch(actions.dragUnscheduledContribs(selected));
      setSelected(new Set());
    } else {
      dispatch(actions.dragUnscheduledContribs(new Set([id])));
    }
  };

  return (
    <Form.Field onClick={() => setSelected(new Set())}>
      {contribs.map(contrib => (
        <DraggableUnscheduledContribution key={contrib.id} id={contrib.id}>
          <ContributionDetails
            key={contrib.id}
            styleName="contribution"
            entry={{...contrib, deleted: true}}
            title={entryTypes.contrib.formatTitle(contrib)}
            uses24HourFormat={uses24HourFormat}
            dispatch={dispatch}
            onDragStart={makeHandleDrag(contrib.id)}
            onClick={makeHandleSelect(contrib.id)}
            selected={selected.has(contrib.id)}
            icon={selected.has(contrib.id) ? 'check square outline' : 'square outline'}
            draggable
          >
            {showSession && contrib.sessionId && (
              <p>
                <Translate as="strong">Session:</Translate>{' '}
                {(sessions.get(contrib.sessionId) || {}).title}
              </p>
            )}
            {!contrib.isPoster && (
              <p>
                <Translate as="strong">Duration:</Translate> {contrib.duration}
              </p>
            )}
          </ContributionDetails>
        </DraggableUnscheduledContribution>
      ))}
    </Form.Field>
  );
}

UnscheduledContributionList.propTypes = {
  contribs: PropTypes.arrayOf(entrySchema).isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  dispatch: PropTypes.func.isRequired,
  selected: PropTypes.instanceOf(Set).isRequired,
  setSelected: PropTypes.func.isRequired,
  showSession: PropTypes.bool,
};

UnscheduledContributionList.defaultProps = {
  showSession: false,
};

export default function UnscheduledContributions() {
  const dispatch = useDispatch();
  const contribs = useSelector(selectors.getUnscheduled);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  // const selectedEntry = useSelector(selectors.getSelectedEntry);
  const selectedEntry = null;

  const [selected, setSelected] = useState(new Set());
  const uses24HourFormat = true; // TODO fix this with localeUses24HourTime

  // ensure that the selections are cleared when the list changes
  useEffect(() => {
    setSelected(new Set());
  }, [contribs]);

  if (!showUnscheduled) {
    return null;
  }

  const [currentContribs, otherContribs] = _.partition(
    _.sortBy(contribs, ['code', 'title']),
    c =>
      c.sessionId === (selectedEntry || {}).sessionId ||
      (!c.sessionId && !(selectedEntry || {}).sessionId)
  );

  return (
    <div styleName="contributions-container">
      <div styleName="content">
        <h4>
          {(selectedEntry || {}).type === 'session'
            ? Translate.string('Unscheduled contributions for session "{sessionName}"', {
                sessionName: formatTitle(selectedEntry.title, selectedEntry.code),
              })
            : Translate.string('Unscheduled contributions with no assigned session')}
          <Icon
            name="close"
            color="black"
            onClick={() => dispatch(actions.toggleShowUnscheduled())}
            title={Translate.string('Hide unscheduled contributions')}
            link
          />
        </h4>
        {currentContribs.length > 0 ? (
          <FinalForm
            onSubmit={values => dispatch(actions.scheduleContribs(values.contribs, values.gap))}
            initialValues={{
              contribs: new Set(),
              gap: 0,
            }}
            subscription={{}}
          >
            {({handleSubmit}) => (
              <Form onSubmit={handleSubmit} style={{position: 'unset'}}>
                <Field name="contribs" isEqual={_.isEqual} format={v => v} parse={v => v}>
                  {({input: {value, onChange}}) => (
                    <UnscheduledContributionList
                      contribs={currentContribs}
                      uses24HourFormat={uses24HourFormat}
                      dispatch={dispatch}
                      selected={value}
                      setSelected={onChange}
                    />
                  )}
                </Field>
                <Field name="contribs" subscription={{value: true}}>
                  {({input: {value}}) => (
                    <>
                      {currentContribs.length > 1 && !(selectedEntry || {}).isPoster && (
                        <FinalInput
                          name="gap"
                          label={Translate.string('Gap between contributions')}
                          componentLabel={{content: Translate.string('minutes', 'duration')}}
                          labelPosition="right"
                          type="number"
                          min="0"
                          step="1"
                          disabled={value.size === 1}
                          fluid
                        />
                      )}
                      <FinalSubmitButton
                        disabledUntilChange={false}
                        label={
                          value.size > 0
                            ? Translate.string('Schedule selected')
                            : Translate.string('Schedule all')
                        }
                        fluid
                      />
                    </>
                  )}
                </Field>
                <p styleName="description">
                  {(selectedEntry || {}).type === 'session' ? (
                    <Translate>
                      The contributions will be scheduled sequentially, in the presented order,
                      after the last contribution inside the selected block (
                      <Param
                        name="blockTitle"
                        value={entryTypes.session.formatTitle(selectedEntry)}
                        wrapper={<strong />}
                      />
                      ) .
                    </Translate>
                  ) : selectedEntry ? (
                    <Translate>
                      The contributions will be scheduled sequentially, in the presented order,
                      after the currently selected entry (
                      <Param
                        name="blockTitle"
                        value={entryTypes[selectedEntry.type].formatTitle(selectedEntry)}
                        wrapper={<strong />}
                      />
                      ) .
                    </Translate>
                  ) : (
                    <Translate>
                      The contributions will be scheduled sequentially, in the presented order,
                      after the last entry on the currently selected day.
                    </Translate>
                  )}
                </p>
              </Form>
            )}
          </FinalForm>
        ) : (
          <p>
            {selectedEntry && selectedEntry.sessionId ? (
              <Translate>
                There are no unscheduled contributions for the selected session.
              </Translate>
            ) : otherContribs.length > 0 ? (
              <Translate>
                There are no unscheduled contributions with no assigned session.
              </Translate>
            ) : (
              <Translate>There are no unscheduled contributions in this event.</Translate>
            )}
          </p>
        )}
        {otherContribs.length > 0 && (
          <CollapsibleContainer
            title={`${Translate.string('Contributions for other sessions')} (${
              otherContribs.length
            })`}
            titleSize="small"
          >
            <UnscheduledContributionList
              contribs={otherContribs}
              uses24HourFormat={uses24HourFormat}
              dispatch={dispatch}
              selected={selected}
              setSelected={setSelected}
              showSession
            />
          </CollapsibleContainer>
        )}
      </div>
    </div>
  );
}
