// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Accordion, Divider, Header, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import AttachmentsDisplay from './components/AttachmentsDisplay';
import DetailsSegment from './components/DetailsSegment';
import EntryColorPicker from './components/EntryColorPicker';
import TimeDisplay from './components/TimeDisplay';
import * as selectors from './selectors';
import {entrySchema, formatTitle, handleUnimplemented, isChildOf} from './util';

import './EntryDetails.module.scss';

const entryIcons = {
  session: 'calendar alternate outline', // XXX: users also looks nice
  contribution: 'file alternate outline',
  break: 'coffee',
};

const detailsPropTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
  dispatch: PropTypes.func.isRequired,
};

function ContributionsDisplay({entry, uses24HourFormat, dispatch}) {
  const children = useSelector(selectors.getChildren);
  const contribs = children.filter(c => isChildOf(c, entry));

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
                dispatch={dispatch}
                showTitle
              />
            )),
          },
        },
      ]}
    />
  );
}

ContributionsDisplay.propTypes = detailsPropTypes;

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
            onClick: () => dispatch(actions.deleteEntry(entry)),
          },
        ]}
      >
        <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
        <Divider />
        <ContributionsDisplay
          entry={entry}
          uses24HourFormat={uses24HourFormat}
          dispatch={dispatch}
        />
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

function ContributionDetails({entry, uses24HourFormat, dispatch, showTitle}) {
  return (
    <DetailsSegment
      title={Translate.string('Contribution')}
      color={entry.color}
      actions={[
        {icon: 'edit', title: Translate.string('Edit contribution'), onClick: handleUnimplemented},
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
        {
          icon: 'trash',
          title: Translate.string('Unschedule contribution'),
          onClick: () => dispatch(actions.deleteEntry(entry)),
        },
      ]}
    >
      {showTitle && (
        <div>
          <Translate as="strong">Title</Translate>: {entry.title}
        </div>
      )}
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
      <AttachmentsDisplay entry={entry} />
    </DetailsSegment>
  );
}

ContributionDetails.propTypes = {
  ...detailsPropTypes,
  showTitle: PropTypes.bool,
};

ContributionDetails.defaultProps = {
  showTitle: false,
};

function BreakDetails({entry, uses24HourFormat, dispatch}) {
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
      dispatch={dispatch}
    >
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
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
    <div styleName="details-container">
      <div styleName="content">
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
    </div>
  );
}
