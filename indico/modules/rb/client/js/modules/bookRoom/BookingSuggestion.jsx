// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Grid, Icon, Label, Message, Popup} from 'semantic-ui-react';

import {PluralTranslate, Translate, Singular, Param, Plural} from 'indico/react/i18n';
import {Slot, IndicoPropTypes} from 'indico/react/util';

import Room from '../../components/Room';

import './BookingSuggestion.module.scss';

function SuggestionOption({onClick, overrides, icon, text, tooltip}) {
  const message = (
    <Message
      styleName="suggestion-text"
      size="mini"
      onClick={onClick.bind(undefined, overrides)}
      warning
      compact
    >
      <Message.Header>
        <Icon name={icon} /> {text}
      </Message.Header>
    </Message>
  );
  return <Popup trigger={message} content={tooltip} position="right center" />;
}

SuggestionOption.propTypes = {
  onClick: PropTypes.func.isRequired,
  overrides: PropTypes.object,
  icon: PropTypes.string.isRequired,
  text: IndicoPropTypes.i18n.isRequired,
  tooltip: IndicoPropTypes.i18n.isRequired,
};

SuggestionOption.defaultProps = {
  overrides: null,
};

/**
 * Renders a "suggested room" containing one or more alternative options
 * e.g. "10 minutes later", "Skip one day"...
 */
export default class BookingSuggestion extends React.PureComponent {
  static propTypes = {
    /** Room information */
    room: PropTypes.object.isRequired,
    /** Suggestions as {time, duration, skip} */
    suggestions: PropTypes.shape({
      time: PropTypes.number,
      duration: PropTypes.number,
      skip: PropTypes.number,
      shorten: PropTypes.number,
    }).isRequired,
    /** Will be called when a suggestion is chosen (clicked on) */
    onClick: PropTypes.func.isRequired,
  };

  getStartTimeSuggestionText(time) {
    return time < 0 ? (
      <PluralTranslate count={time}>
        <Singular>One minute earlier</Singular>
        <Plural>
          <Param name="count" value={Math.abs(time)} /> minutes earlier
        </Plural>
      </PluralTranslate>
    ) : (
      <PluralTranslate count={time}>
        <Singular>One minute later</Singular>
        <Plural>
          <Param name="count" value={time} /> minutes later
        </Plural>
      </PluralTranslate>
    );
  }

  renderSuggestionText(room, {time, duration, skip, shorten}) {
    const {onClick} = this.props;
    return (
      <>
        {time && (
          <SuggestionOption
            onClick={onClick}
            overrides={{time}}
            icon="clock"
            text={this.getStartTimeSuggestionText(time)}
            tooltip={Translate.string("We'll change your booking's starting time to make it fit")}
          />
        )}
        {duration && time && (
          <div>
            <Label color="brown" circular>
              {Translate.string('or')}
            </Label>
          </div>
        )}
        {duration && (
          <SuggestionOption
            onClick={onClick}
            overrides={{duration}}
            icon="hourglass full"
            text={PluralTranslate.string(
              'One minute shorter',
              '{duration} minutes shorter',
              duration,
              {duration}
            )}
            tooltip={Translate.string("We'll shorten your booking to make it fit")}
          />
        )}
        {skip && (
          <SuggestionOption
            onClick={onClick}
            icon="calendar times"
            text={PluralTranslate.string('Skip one day', 'Skip {skip} days', skip, {skip})}
            tooltip={PluralTranslate.string(
              "We'll skip one occurrence to avoid any conflicts",
              "We'll skip {skip} occurrences to avoid any conflicts",
              skip,
              {skip}
            )}
          />
        )}
        {shorten && (
          <SuggestionOption
            onClick={onClick}
            overrides={{shorten}}
            icon="calendar times"
            text={PluralTranslate.string(
              'Shorten by one day',
              'Shorten by {shorten} days',
              shorten,
              {shorten}
            )}
            tooltip={Translate.string(
              'Bookings in this room cannot last this long and will be shortened accordingly'
            )}
          />
        )}
      </>
    );
  }

  render() {
    const {room, suggestions} = this.props;
    return (
      <Room key={room.id} room={room}>
        <Slot>
          <Grid centered styleName="suggestion" columns={3}>
            <Grid.Column verticalAlign="middle" width={14}>
              {this.renderSuggestionText(room, suggestions)}
            </Grid.Column>
          </Grid>
        </Slot>
      </Room>
    );
  }
}
