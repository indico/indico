// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Header, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import AttachmentsDisplay from './components/AttachmentsDisplay';
import DetailsSegment from './components/DetailsSegment';
import EntryColorPicker from './components/EntryColorPicker';
import TimeDisplay from './components/TimeDisplay';
import * as selectors from './selectors';
import {entrySchema} from './util';

import './EntryDetails.module.scss';

const entryIcons = {
  session: 'calendar alternate outline', // XXX: users also looks nice
  contribution: 'file alternate outline',
  break: 'coffee',
};

const formatTitle = (title, code) => (code ? `${title} (${code})` : title);

const detailsPropTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  dispatch: PropTypes.func.isRequired,
};

// TODO remove
// eslint-disable-next-line no-alert
export const handleUnimplemented = () => alert('desole, ça marche pas encore :(');

function SessionDetails({entry, uses24HourFormat, dispatch}) {
  const {title, slotTitle, code, color} = entry;
  return (
    <>
      <DetailsSegment
        title={Translate.string('Block')}
        subtitle={slotTitle}
        actions={[
          {icon: 'edit', title: Translate.string('Edit session block')},
          {
            icon: 'trash',
            title: Translate.string('Delete session block'),
          },
        ]}
      >
        <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} dispatch={dispatch} />
      </DetailsSegment>
      <DetailsSegment
        title={Translate.string('Session')}
        subtitle={formatTitle(title, code)}
        color={color}
        actions={[
          {icon: 'paint brush', title: Translate.string('Change color'), wrapper: EntryColorPicker},
          {icon: 'edit', title: Translate.string('Edit session'), onClick: handleUnimplemented},
          {
            icon: 'shield',
            title: Translate.string('Manage session protection'),
            onClick: handleUnimplemented,
          },
        ]}
        entry={entry}
        dispatch={dispatch}
      >
        <AttachmentsDisplay entry={entry} />
      </DetailsSegment>
    </>
  );
}

SessionDetails.propTypes = detailsPropTypes;

function ContributionDetails({entry, uses24HourFormat, dispatch}) {
  return (
    <DetailsSegment
      title={Translate.string('Contribution')}
      color={entry.color}
      actions={[
        {icon: 'edit', title: Translate.string('Edit contribution'), onClick: handleUnimplemented},
        {
          icon: 'trash',
          title: Translate.string('Delete contribution'),
          onClick: handleUnimplemented,
        },
      ]}
    >
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} dispatch={dispatch} />
      <AttachmentsDisplay entry={entry} />
    </DetailsSegment>
  );
}

ContributionDetails.propTypes = detailsPropTypes;

function BreakDetails({entry, uses24HourFormat, dispatch}) {
  return (
    <DetailsSegment
      title={Translate.string('Break')}
      color={entry.color}
      actions={[
        {icon: 'edit', title: Translate.string('Edit break'), onClick: handleUnimplemented},
        {
          icon: 'trash',
          title: Translate.string('Delete break'),
          onClick: handleUnimplemented,
        },
      ]}
    >
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} dispatch={dispatch} />
    </DetailsSegment>
  );
}

BreakDetails.propTypes = detailsPropTypes;

export default function EntryDetails() {
  const dispatch = useDispatch();
  const entry = useSelector(selectors.getSelectedEntry);
  const {title, slotTitle, description, code, sessionCode, type} = entry;

  // TODO figure this out:
  const uses24HourFormat = true;

  const PopupContentComponent = {
    session: SessionDetails,
    contribution: ContributionDetails,
    break: BreakDetails,
  }[type];

  return (
    <div styleName="details">
      <Icon
        name="close"
        color="black"
        className="right"
        onClick={() => dispatch(actions.selectEntry(null))}
        title={Translate.string('Close details')}
        link
      />
      <Header
        size="small"
        color="blue"
        icon={entryIcons[type]}
        content={formatTitle(title, code)}
        subheader={formatTitle(slotTitle, sessionCode)}
      />
      {description && <div styleName="description">{description}</div>}
      <PopupContentComponent
        entry={entry}
        uses24HourFormat={uses24HourFormat}
        dispatch={dispatch}
      />
    </div>
  );
}
