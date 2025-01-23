// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Accordion, Divider, Header, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import AttachmentsDisplay from './components/AttachmentsDisplay';
import DetailsSegment from './components/DetailsSegment';
import EntryColorPicker from './components/EntryColorPicker';
import TimeDisplay from './components/TimeDisplay';
import {useTimetableDispatch} from './hooks';
import {Entry} from './types';
import {entryTypes, formatTitle, handleUnimplemented} from './util';

import './EntryDetails.module.scss';

const entryIcons = {
  session: 'calendar alternate outline', // XXX: users also looks nice
  contrib: 'file alternate outline',
  break: 'coffee',
};

interface DetailsProps {
  entry: Entry;
  uses24HourFormat: boolean;
}

function ContributionsDisplay({entry, uses24HourFormat}: DetailsProps) {
  const contribs = entry.children;

  if (contribs.length === 0) {
    return (
      <p>
        <Translate as="strong">Contributions</Translate>: <Icon name="file alternate outline" />
        <Translate as="em">None</Translate>
      </p>
    );
  }

  return (
    <Accordion
      panels={[
        {
          key: 'contribs',
          title: {
            content: (
              <>
                <Translate as="strong">Contributions</Translate>:{' '}
                <Icon name="file alternate outline" />
                {contribs.length}
              </>
            ),
            icon: null,
          },
          content: {
            content: contribs.map(contrib => (
              <ContributionDetails
                key={contrib.id}
                entry={contrib}
                uses24HourFormat={uses24HourFormat}
                title={entryTypes.contrib.formatTitle(contrib)}
              />
            )),
          },
        },
      ]}
    />
  );
}

function SessionDetails({entry, uses24HourFormat}: DetailsProps) {
  const {title, slotTitle, code, sessionCode, color} = entry;
  const dispatch = useTimetableDispatch();
  return (
    <>
      <DetailsSegment
        title={Translate.string('Block')}
        subtitle={formatTitle(slotTitle, sessionCode)}
        actions={[
          {icon: 'edit', title: Translate.string('Edit session block')},
          {
            icon: 'trash',
            title: Translate.string('Delete session block'),
            onClick: () => dispatch(actions.deleteEntry(entry)),
          },
        ]}
      >
        <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
        <Divider />
        <ContributionsDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
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
      >
        <AttachmentsDisplay entry={entry} />
      </DetailsSegment>
    </>
  );
}

interface ContributionDetailsProps extends DetailsProps {
  children?: React.ReactNode;
}

export function ContributionDetails({
  entry,
  uses24HourFormat,
  children,
  ...rest
}: ContributionDetailsProps) {
  const dispatch = useTimetableDispatch();
  const contribActions = [
    {
      icon: 'edit',
      title: Translate.string('Edit contribution'),
      onClick: () => dispatch(actions.editEntry({type: 'contribution', entry})),
    },
    {
      icon: 'shield',
      title: Translate.string('Manage contribution protection'),
      onClick: handleUnimplemented,
    },
    {
      icon: 'clone outline',
      title: Translate.string('Clone contribution'),
      onClick: handleUnimplemented,
    },
  ];
  if (!entry.deleted) {
    contribActions.push({
      icon: 'trash',
      title: Translate.string('Unschedule contribution'),
      onClick: () => dispatch(actions.deleteEntry(entry)),
    });
  }

  return (
    <DetailsSegment
      title={Translate.string('Contribution')}
      color={entry.color}
      actions={contribActions}
      {...rest}
    >
      {children || (
        <>
          {!entry.isPoster && <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />}
          <AttachmentsDisplay entry={entry} />
        </>
      )}
    </DetailsSegment>
  );
}

function BreakDetails({entry, uses24HourFormat}: ContributionDetailsProps) {
  const dispatch = useTimetableDispatch();
  return (
    <DetailsSegment
      title={Translate.string('Break')}
      color={entry.color}
      actions={[
        {icon: 'paint brush', title: Translate.string('Change color'), wrapper: EntryColorPicker},
        {icon: 'edit', title: Translate.string('Edit break'), onClick: handleUnimplemented},
        {
          icon: 'trash',
          title: Translate.string('Delete break'),
          onClick: () => dispatch(actions.deleteEntry(entry)),
        },
      ]}
      entry={entry}
    >
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
    </DetailsSegment>
  );
}

export default function EntryDetails({entry}: {entry: Entry}) {
  const dispatch = useTimetableDispatch();
  const {title, slotTitle, description, code, sessionCode, type} = entry;
  // TODO figure this out:
  const uses24HourFormat = true;

  const PopupContentComponent = {
    block: SessionDetails,
    contrib: ContributionDetails,
    break: BreakDetails,
  }[type];

  return (
    <div styleName="details-container">
      <div styleName="content">
        <div style={{display: 'flex', justifyContent: 'space-between'}}>
          <Header
            size="small"
            color="blue"
            icon={entryIcons[type]}
            content={formatTitle(title, code)}
            subheader={formatTitle(slotTitle, sessionCode)}
          />
          <Icon
            name="close"
            color="black"
            onClick={() => dispatch(actions.selectEntry(null))}
            title={Translate.string('Close details')}
            link
          />
        </div>
        {description && <div styleName="description">{description}</div>}
        <PopupContentComponent entry={entry} uses24HourFormat={uses24HourFormat} />
      </div>
    </div>
  );
}
