// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Confirm, Icon, Label, List, Modal} from 'semantic-ui-react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import * as actions from '../actions';
import * as selectors from '../selectors';
import {entryColorSchema, entrySchema, entryTypes, isChildOf} from '../util';

import DetailsSegment from './DetailsSegment';

import './SaveButton.module.scss';

function DiffLabel({diff, children}) {
  return (
    <Label color="red" size="tiny" horizontal>
      {diff > 0 ? '+' : '-'}
      {children}
    </Label>
  );
}

DiffLabel.propTypes = {
  diff: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
};

const renderDateDiff = (oldValue, newValue) => {
  const diff = moment(newValue).diff(moment(oldValue), 'days');
  return (
    <DiffLabel diff={diff}>
      <PluralTranslate count={Math.abs(diff)}>
        <Singular>
          <Param name="count" value={Math.abs(diff)} /> day
        </Singular>
        <Plural>
          <Param name="count" value={Math.abs(diff)} /> days
        </Plural>
      </PluralTranslate>
    </DiffLabel>
  );
};

const renderTimeDiff = (oldValue, newValue) => {
  const hours = moment(newValue).diff(moment(oldValue), 'hours');
  const minutes = moment(newValue).diff(moment(oldValue), 'minutes');
  return (
    <DiffLabel diff={newValue - oldValue}>
      {Math.abs(hours)}:{Math.abs(minutes) % 60}
    </DiffLabel>
  );
};

const renderDurationDiff = (oldValue, newValue) => {
  const diff = newValue - oldValue;
  return (
    <DiffLabel diff={diff}>
      <PluralTranslate count={Math.abs(diff)}>
        <Singular>
          <Param name="count" value={Math.abs(diff)} /> minute
        </Singular>
        <Plural>
          <Param name="count" value={Math.abs(diff)} /> minutes
        </Plural>
      </PluralTranslate>
    </DiffLabel>
  );
};

const changeParams = {
  startDate: {
    title: Translate.string('Start date'),
    renderValue: value => moment(value).format('L'),
    renderDiff: renderDateDiff,
  },
  startTime: {
    title: Translate.string('Start time'),
    renderValue: value => moment(value).format('LT'),
    renderDiff: renderTimeDiff,
  },
  duration: {
    title: Translate.string('Duration'),
    renderValue: value => value,
    renderDiff: renderDurationDiff,
  },
  color: {
    title: Translate.string('Color'),
    renderValue: value => (
      <Label
        icon="paint brush"
        style={{backgroundColor: value.background, color: value.text}}
        circular
      />
    ),
  },
  columnId: {
    title: Translate.string('Display order'),
    renderValue: value => value,
    skip: (oldValue, newValue) => !oldValue || !newValue,
  },
  parent: {
    title: Translate.string('Parent block'),
    renderValue: value =>
      value.id ? (
        <Label
          icon={entryTypes.session.icon}
          content={entryTypes.session.formatTitle(value)}
          style={{backgroundColor: value.color?.background, color: value.color?.text}}
        />
      ) : (
        Translate.string('None')
      ),
  },
  deleted: {
    renderDiff: () => (
      <p>
        <Icon name="exclamation triangle" color="red" />
        <Translate>This entry has been deleted from the timetable.</Translate>
      </p>
    ),
  },
};

function Change({param, oldValue, newValue}) {
  const changeParam = changeParams[param];
  if (!changeParam || !oldValue || !newValue) {
    // TODO remove this check when fully implemented
    console.error('you forgot to implement this one!', param, oldValue, newValue);
    return null;
  }
  if (changeParam.skip && changeParam.skip(oldValue, newValue)) {
    return null;
  }
  return (
    <List.Item>
      {changeParam.title && <Label content={changeParam.title} horizontal />}
      {changeParam.renderValue && (
        <div styleName="change">
          {changeParam.renderValue(oldValue)}
          <Icon name="long arrow alternate right" />
          {changeParam.renderValue(newValue)}
        </div>
      )}
      {changeParam.renderDiff && changeParam.renderDiff(oldValue, newValue)}
    </List.Item>
  );
}

Change.propTypes = {
  param: PropTypes.string.isRequired,
  oldValue: PropTypes.any.isRequired,
  newValue: PropTypes.any.isRequired,
};

function EntryChangeList({change, old, entry, color, children, ...rest}) {
  const blocks = useSelector(selectors.getBlocks);
  const {title, icon, formatTitle} = entryTypes[entry.type];
  return (
    <DetailsSegment title={formatTitle(entry)} subtitle={title} color={color} icon={icon} {...rest}>
      <List divided>
        {Object.entries(change)
          .flatMap(([key, value]) => {
            const newValue = {oldValue: old[key], newValue: value};
            switch (key) {
              case 'start':
                // we split date and time changes into separate keys
                return [
                  value.toDateString() !== old[key].toDateString() && [`${key}Date`, newValue],
                  value.toTimeString() !== old[key].toTimeString() && [`${key}Time`, newValue],
                ].filter(x => x);
              case 'end':
                // let's replace it with the duration instead
                newValue.oldValue = moment(old.end).diff(moment(old.start), 'minutes');
                newValue.newValue = moment(value).diff(moment(entry.start), 'minutes');
                return newValue.oldValue === newValue.newValue ? [] : [['duration', newValue]];
              case 'parentId':
                return [
                  [
                    'parent',
                    {
                      oldValue: old.parentId ? blocks.find(b => isChildOf(old, b)) : {},
                      newValue: value ? blocks.find(b => b.id === value) : {},
                    },
                  ],
                ];
              case 'columnId':
                return Object.values(newValue).every(x => x) ? [[key, newValue]] : [];
              default:
                return [[key, newValue]];
            }
          })
          .map(([key, value]) => (
            <Change key={key} param={key} {...value} />
          ))}
      </List>
      {children}
    </DetailsSegment>
  );
}

EntryChangeList.propTypes = {
  change: PropTypes.object.isRequired,
  old: entrySchema.isRequired,
  entry: entrySchema.isRequired,
  color: entryColorSchema,
  children: PropTypes.node,
};

EntryChangeList.defaultProps = {
  color: null,
  children: null,
};

export default function SaveButton({as: Component, ...rest}) {
  const dispatch = useDispatch();
  const [open, setOpen] = useState(false);
  const changes = useSelector(selectors.getMergedChanges);
  const blocks = useSelector(selectors.getBlocks);
  const blockChanges = _.sortBy(
    [
      ...changes.filter(({entry}) => !entry.parentId),
      ...blocks
        .filter(
          block =>
            !changes.some(({entry}) => entry.id === block.id) &&
            changes.some(({entry}) => isChildOf(entry, block))
        )
        .map(block => ({change: {}, old: block, entry: block})),
    ],
    [({entry}) => entry.start, ({entry}) => entry.columnId]
  );

  return (
    <>
      <Confirm
        open={open}
        header={Translate.string('Review and save changes')}
        onConfirm={() => {
          dispatch(actions.saveChanges());
          setOpen(false);
        }}
        onCancel={() => setOpen(false)}
        confirmButton={Translate.string('Save')}
        content={
          <Modal.Content styleName="changelog">
            {blockChanges.map(({change, old, entry}) => (
              <EntryChangeList
                key={entry.id}
                change={change}
                old={old}
                entry={entry}
                color={entry.color}
                raised
              >
                {changes
                  .filter(({entry: child}) => isChildOf(child, entry))
                  .map(({change: childChange, old: childOld, entry: child}) => (
                    <EntryChangeList
                      key={child.id}
                      change={childChange}
                      old={childOld}
                      entry={child}
                      color={entry.color}
                    />
                  ))}
              </EntryChangeList>
            ))}
          </Modal.Content>
        }
      />
      <Component
        onClick={() => setOpen(true)}
        content={Translate.string('Save')}
        title={Translate.string('Review and save changes')}
        icon={changes.length > 0 && {name: 'exclamation triangle', color: 'red'}}
        disabled={changes.length === 0}
        {...rest}
      />
    </>
  );
}

SaveButton.propTypes = {
  as: PropTypes.elementType.isRequired,
};
