// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Accordion, Form, Header, Icon, Label, Popup, Segment} from 'semantic-ui-react';

import {FinalCheckbox, FinalField, FinalSubmitButton} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import * as selectors from './selectors';
import {isChildOf} from './util';

import './EntryPopup.module.scss';

const entryColorSchema = PropTypes.shape({
  text: PropTypes.string,
  background: PropTypes.string,
});

const entrySchema = PropTypes.shape({
  id: PropTypes.string.isRequired,
  type: PropTypes.oneOf(['session', 'contribution', 'break']).isRequired,
  title: PropTypes.string.isRequired,
  slotTitle: PropTypes.string, // only for sessions
  description: PropTypes.string,
  code: PropTypes.string,
  sessionCode: PropTypes.string, // only for sessions
  start: PropTypes.instanceOf(Date).isRequired,
  end: PropTypes.instanceOf(Date).isRequired,
  color: entryColorSchema,
  attachmentCount: PropTypes.number,
  displayOrder: PropTypes.number,
  parentId: PropTypes.string, // only for contributions
  resourceId: PropTypes.number,
});

const entryIcons = {
  session: 'calendar alternate outline', // XXX: users also looks nice
  contribution: 'file alternate outline',
  break: 'coffee',
};

const formatTitle = (title, code) => (code ? `${title} (${code})` : title);

function LinkTimePicker({value, onChange, uses24HourFormat}) {
  return (
    <Form.Field>
      <TimePicker
        showSecond={false}
        value={moment(value)}
        focusOnOpen
        format={uses24HourFormat ? 'H:mm' : 'h:mm a'}
        onChange={onChange}
        use12Hours={!uses24HourFormat}
        allowEmpty={false}
        getPopupContainer={node => node}
      />
    </Form.Field>
  );
}

LinkTimePicker.propTypes = {
  value: PropTypes.instanceOf(Date).isRequired,
  onChange: PropTypes.func.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

function TimeEditForm({entry, uses24HourFormat}) {
  const {start, end} = entry;
  const onSubmit = () => {};
  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={{
        start,
        duration: moment(end).diff(start, 'minutes'),
        shift: false,
      }}
      initialValuesEqual={_.isEqual}
    >
      {({handleSubmit}) => (
        <Form id="time-edit-form" onSubmit={handleSubmit}>
          <Form.Group>
            <FinalField
              name="start"
              label={Translate.string('Start time')}
              component={LinkTimePicker}
              uses24HourFormat={uses24HourFormat}
            />
            <FinalField
              name="duration"
              label={Translate.string('Duration')}
              component={LinkTimePicker}
              uses24HourFormat={uses24HourFormat}
            />
          </Form.Group>
          <FinalCheckbox
            name="shift"
            label={Translate.string('Shift')}
            description={Translate.string('Shift all entries after this one up or down')}
          />
          <FinalSubmitButton form="time-edit-form" label={Translate.string('Apply changes')} />
        </Form>
      )}
    </FinalForm>
  );
}

TimeEditForm.propTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

function TimeDisplay({entry, uses24HourFormat}) {
  return (
    <Accordion
      panels={[
        {
          key: 'time',
          title: {
            content: (
              <>
                {moment(entry.start).format('HH:mm')} - {moment(entry.end).format('HH:mm')}
                <Popup
                  content={Translate.string('Change time')}
                  trigger={<Icon name="pencil" color="grey" className="right" link />}
                />
              </>
            ),
            icon: 'clock outline',
          },
          content: {
            content: <TimeEditForm entry={entry} uses24HourFormat={uses24HourFormat} />,
          },
        },
      ]}
    />
  );
}

TimeDisplay.propTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

function AttachmentsDisplay({entry}) {
  const {attachmentCount} = entry;
  return (
    <p>
      <Translate as="strong">Materials</Translate>: <Icon name="paperclip" />
      {attachmentCount > 0 ? (
        <PluralTranslate count={attachmentCount}>
          <Singular>
            <Param name="count" value={attachmentCount} /> file
          </Singular>
          <Plural>
            <Param name="count" value={attachmentCount} /> files
          </Plural>
        </PluralTranslate>
      ) : (
        <Translate as="em">None</Translate>
      )}
      <Popup
        content={Translate.string('Manage materials')}
        trigger={<Icon name="pencil" color="grey" className="right" link />}
      />
    </p>
  );
}

AttachmentsDisplay.propTypes = {
  entry: entrySchema.isRequired,
};

function EntryPopupSegment({title, subtitle, color, actions, children}) {
  return (
    <Segment style={{borderColor: color?.background}}>
      <Label
        style={{backgroundColor: color?.background, color: color?.text}}
        styleName="segment-header"
        attached="top"
      >
        <Translate>{title}</Translate>
        {subtitle && <Label.Detail>{subtitle}</Label.Detail>}
        <div styleName="actions">
          {actions.map(action => (
            <Popup
              key={action.icon}
              trigger={
                <Icon
                  name={action.icon}
                  onClick={action.onCLick}
                  style={{color: color?.text || 'rgba(0, 0, 0, 0.6)'}}
                  link
                />
              }
              content={action.label}
            />
          ))}
        </div>
      </Label>
      {children}
    </Segment>
  );
}

EntryPopupSegment.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  color: entryColorSchema,
  actions: PropTypes.arrayOf(
    PropTypes.shape({
      icon: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      onClick: PropTypes.func.isRequired,
    })
  ).isRequired,
  children: PropTypes.node.isRequired,
};

EntryPopupSegment.defaultProps = {
  subtitle: '',
  color: {},
};

const popupContentPropTypes = {
  entry: entrySchema.isRequired,
  uses24HourFormat: PropTypes.bool.isRequired,
};

function SessionPopupContent({entry, uses24HourFormat}) {
  const {title, slotTitle, code, color} = entry;
  return (
    <>
      <EntryPopupSegment
        title={Translate.string('Block')}
        subtitle={slotTitle}
        actions={[
          {icon: 'edit', label: Translate.string('Edit session block'), onClick: () => {}},
          {
            icon: 'trash',
            label: Translate.string('Delete session block'),
            onClick: () => {},
          },
        ]}
      >
        <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
      </EntryPopupSegment>
      <EntryPopupSegment
        title={Translate.string('Session')}
        subtitle={formatTitle(title, code)}
        color={color}
        actions={[
          {icon: 'paint brush', label: Translate.string('Change color'), onClick: () => {}},
          {icon: 'edit', label: Translate.string('Edit session'), onClick: () => {}},
          {
            icon: 'shield',
            label: Translate.string('Manage session protection'),
            onClick: () => {},
          },
        ]}
      >
        <AttachmentsDisplay entry={entry} />
      </EntryPopupSegment>
    </>
  );
}

SessionPopupContent.propTypes = popupContentPropTypes;

function ContributionPopupContent({entry, uses24HourFormat}) {
  return (
    <EntryPopupSegment
      title={Translate.string('Contribution')}
      color={entry.color}
      actions={[
        {icon: 'edit', label: Translate.string('Edit contribution'), onClick: () => {}},
        {
          icon: 'trash',
          label: Translate.string('Delete contribution'),
          onClick: () => {},
        },
      ]}
    >
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
      <AttachmentsDisplay entry={entry} />
    </EntryPopupSegment>
  );
}

ContributionPopupContent.propTypes = popupContentPropTypes;

function BreakPopupContent({entry, uses24HourFormat}) {
  return (
    <EntryPopupSegment
      title={Translate.string('Break')}
      color={entry.color}
      actions={[
        {icon: 'edit', label: Translate.string('Edit break'), onClick: () => {}},
        {
          icon: 'trash',
          label: Translate.string('Delete break'),
          onClick: () => {},
        },
      ]}
    >
      <TimeDisplay entry={entry} uses24HourFormat={uses24HourFormat} />
    </EntryPopupSegment>
  );
}

BreakPopupContent.propTypes = popupContentPropTypes;

export default function EntryPopup({event: entry}) {
  const {title, slotTitle, description, code, sessionCode, type} = entry;
  const contributions = useSelector(selectors.getContributions);
  const displayMode = useSelector(selectors.getDisplayMode);
  const hasContribs = contributions.some(c => isChildOf(c, entry));

  // TODO figure this out:
  const uses24HourFormat = true;

  const PopupContentComponent = {
    session: SessionPopupContent,
    contribution: ContributionPopupContent,
    break: BreakPopupContent,
  }[type];

  return (
    <>
      {displayMode === 'compact' && hasContribs && <div styleName="compact-title">{title}</div>}
      <Popup
        on="click"
        content={
          <div styleName="popup">
            <Header
              size="small"
              color="blue"
              icon={entryIcons[type]}
              content={formatTitle(title, code)}
              subheader={formatTitle(slotTitle, sessionCode)}
            />
            {description && <div styleName="description">{description}</div>}
            <PopupContentComponent entry={entry} uses24HourFormat={uses24HourFormat} />
          </div>
        }
        trigger={
          <div styleName="entry-title">
            {(displayMode === 'full' || !hasContribs) && [
              title,
              slotTitle && `: ${slotTitle}`,
              code && ` (${code})`,
            ]}
          </div>
        }
        flowing
      />
    </>
  );
}

EntryPopup.propTypes = {
  event: entrySchema.isRequired,
};
