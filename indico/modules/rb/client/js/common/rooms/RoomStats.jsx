// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getRoomStatsDataURL from 'indico-url:rb.room_stats';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Header, Grid, Placeholder} from 'semantic-ui-react';

import {Translate, Param, PluralTranslate, Singular, Plural} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import './RoomStats.module.scss';

export default class RoomStats extends React.PureComponent {
  static propTypes = {
    roomId: PropTypes.number.isRequired,
  };

  state = {
    loaded: false,
    data: {},
  };

  componentDidMount() {
    const {roomId} = this.props;
    this.fetchStatsData(roomId);
  }

  async fetchStatsData(roomId) {
    let response;
    try {
      response = await indicoAxios.get(getRoomStatsDataURL({room_id: roomId}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    this.setState({
      loaded: true,
      data: camelizeKeys(response.data),
    });
  }

  renderPlaceholder() {
    return (
      <Grid columns={2} stackable>
        {_.range(0, 2).map(i => (
          <Grid.Column key={i}>
            <Placeholder styleName="placeholder">
              <Placeholder.Line length="long" />
              {_.range(0, 3).map(j => (
                <Placeholder.Paragraph key={j}>
                  <Placeholder.Line length="medium" />
                  <Placeholder.Line length="very short" />
                </Placeholder.Paragraph>
              ))}
            </Placeholder>
          </Grid.Column>
        ))}
      </Grid>
    );
  }

  render() {
    const {loaded, data} = this.state;
    const sections = {
      times_booked: {title: Translate.string('Times booked')},
      occupancy: {
        title: Translate.string('Occupancy'),
        note: Translate.string('excluding weekends'),
      },
    };
    const hasStats = Object.values(data)
      .map(({values}) => values)
      .some(values => !!values.length);

    if (!loaded) {
      return this.renderPlaceholder();
    }
    return (
      hasStats && (
        <>
          <Header>
            <Translate>Statistics</Translate>
          </Header>
          <div styleName="room-stats">
            {Object.entries(data).map(([key, {id, values, note}]) => (
              <div key={key} styleName="stats-box">
                <div styleName="title">
                  {sections[id].title}
                  {note && '*'}
                </div>
                {values.map(({days, value}) => (
                  <div styleName="value-box" key={`${days}-${value}`}>
                    <div styleName="days">
                      <PluralTranslate count={days}>
                        <Singular>Last day</Singular>
                        <Plural>
                          Last <Param name="days" value={days} /> days
                        </Plural>
                      </PluralTranslate>
                    </div>
                    <div styleName="value">
                      {Math.round(value)}
                      {key === 'percentage' ? '%' : ''}
                    </div>
                  </div>
                ))}
                {note && <div styleName="note">* {sections[id].note}</div>}
              </div>
            ))}
          </div>
        </>
      )
    );
  }
}
