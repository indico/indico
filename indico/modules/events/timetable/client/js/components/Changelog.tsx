// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Label, List, Modal} from 'semantic-ui-react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import {useTimetableSelector} from '../hooks';
import * as selectors from '../selectors';
import {entryColorSchema, entrySchema, entryTypes, isChildOf} from '../util';

import DetailsSegment from './DetailsSegment';

import './Changelog.module.scss';

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
  const diff = newValue.diff(oldValue, 'days');
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
  const hours = moment(newValue).diff(moment(oldValue), 'hours') % 24;
  const minutes = moment(newValue).diff(moment(oldValue), 'minutes') % 60;
  return (
    <DiffLabel diff={hours || minutes}>
      {String(Math.abs(hours)).padStart(2, '0')}:{String(Math.abs(minutes)).padStart(2, '0')}
    </DiffLabel>
  );
};

const renderDuration = duration =>
  PluralTranslate.string('{duration} minute', '{duration} minutes', duration, {duration});

const renderDurationDiff = (oldValue, newValue) => {
  const diff = newValue - oldValue;
  return <DiffLabel diff={diff}>{renderDuration(Math.abs(diff))}</DiffLabel>;
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
    renderValue: renderDuration,
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
  unscheduled: {
    renderDiff: () => (
      <p>
        <Icon name="exclamation triangle" color="red" />
        <Translate>This entry has been unscheduled from the timetable.</Translate>
      </p>
    ),
  },
};

function Change({param, oldValue, newValue}) {
  const changeParam = changeParams[param];
  if (!changeParam) {
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

function EntryChangeList({change, old, new: new_, color, children, ...rest}) {
  const blocks = useTimetableSelector(selectors.getBlocks);
  const {title, icon, formatTitle} = entryTypes[new_.type];
  return (
    <DetailsSegment title={formatTitle(new_)} subtitle={title} color={color} icon={icon} {...rest}>
      <List divided>
        {Object.entries(change)
          .flatMap(([key, value]) => {
            const newChange = {oldValue: key in old ? old[key] : null, newValue: value};
            switch (key) {
              case 'start':
                if (!value) {
                  return [['unscheduled', {oldValue: false, newValue: true}]];
                }
                return [
                  value.toDateString() !== old.start?.toDateString() && ['startDate', newChange],
                  value.toTimeString() !== old.start?.toTimeString() && ['startTime', newChange],
                ].filter(x => x);
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
                return Object.values(newChange).every(x => x) ? [[key, newChange]] : [];
              default:
                return [[key, newChange]];
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
  new: entrySchema.isRequired,
  color: entryColorSchema,
  children: PropTypes.node,
};

EntryChangeList.defaultProps = {
  color: null,
  children: null,
};

export default function ReviewChangesButton({as: Component, ...rest}) {
  const changesMap = useTimetableSelector(selectors.getMergedChanges);
  const blocks = useTimetableSelector(selectors.getBlocks);
  const changes = Object.values(changesMap);
  const blockChanges = _.sortBy(
    [
      ...changes.filter(({new: e}) => !e.parentId),
      ...blocks
        .filter(
          block => !(block.id in changesMap) && changes.some(({new: e}) => isChildOf(e, block))
        )
        .map(block => ({old: block, new: block, change: {}})),
    ],
    [c => c.new.start, c => c.new.columnId]
  );

  return (
    <Modal
      trigger={
        <Component
          title={Translate.string('Review changes')}
          disabled={changes.length === 0}
          {...rest}
        >
          <Icon name="history" />
          {changes.length > 0 && (
            <Label color="red" size="mini" content={changes.length} circular floating />
          )}
        </Component>
      }
      header={Translate.string('Review changes')}
      content={
        <Modal.Content styleName="changelog">
          {blockChanges.map(b => (
            <EntryChangeList key={b.new.id} {...b} color={b.new.color} raised>
              {changes
                .filter(c => isChildOf(c.new, b.new))
                .map(c => (
                  <EntryChangeList key={c.new.id} {...c} color={b.new.color} />
                ))}
            </EntryChangeList>
          ))}
        </Modal.Content>
      }
      actions={[Translate.string('Close')]}
    />
  );
}

ReviewChangesButton.propTypes = {
  as: PropTypes.elementType.isRequired,
};
