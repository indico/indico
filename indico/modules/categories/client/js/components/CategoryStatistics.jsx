// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryStatisticsURL from 'indico-url:categories.statistics_json';

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useContext, useMemo} from 'react';
import {Chart} from 'react-charts';
import {Container, Header, Segment, Statistic, Message, Loader} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';

import {LocaleContext} from '../context.js';
import './CategoryStatistics.module.scss';

export default function CategoryStatistics({categoryId}) {
  const {data, loading: isLoading} = useIndicoAxios(
    {url: categoryStatisticsURL({category_id: categoryId})},
    {camelize: true}
  );

  if (isLoading) {
    return <Loader size="massive" active />;
  } else if (!data) {
    return null;
  }

  return <CategoryStatisticsDisplay data={data} />;
}

CategoryStatistics.propTypes = {
  categoryId: PropTypes.number.isRequired,
};

function getGraphData(data) {
  const serialize = statsData => {
    const maxDate = parseInt(
      Object.keys(statsData)
        .reverse()
        .find(date => date <= data.maxYear + 3),
      10
    );
    return [
      [moment(data.minYear - 1, 'YYYY'), null],
      ...Object.entries(statsData)
        .filter(([year]) => year <= maxDate && year >= data.minYear)
        .map(([year, number]) => [moment(year, 'YYYY'), number]),
      [moment(maxDate + 1, 'YYYY'), null],
    ];
  };

  const series = {type: 'bar'};
  const tooltip = {align: 'left', anchor: 'left'};
  const axes = [
    {primary: true, type: 'time', position: 'bottom'},
    {type: 'linear', position: 'left'},
  ];
  const eventGraph = [
    {
      label: Translate.string('Events'),
      data: serialize(data.events),
    },
  ];
  const contributionsGraph = [
    {
      label: Translate.string('Contributions'),
      data: serialize(data.contributions),
    },
  ];

  return {eventGraph, contributionsGraph, series, axes, tooltip};
}

function CategoryStatisticsDisplay({data}) {
  const lang = useContext(LocaleContext);
  const userLanguage = lang.replace('_', '-');
  const updatedTime = moment
    .utc(data.updated)
    .local()
    .format('LLL');
  const fmt = new Intl.NumberFormat(userLanguage);
  const totalEvents = fmt.format(data.totalEvents);
  const totalContributions = fmt.format(data.totalContributions);
  const files = fmt.format(data.files);
  const users = fmt.format(data.users);
  const {eventGraph, contributionsGraph, series, axes, tooltip} = useMemo(
    () => getGraphData(data),
    [data]
  );

  return (
    <Container>
      <Segment.Group horizontal>
        <Segment>
          <Header as="h2">
            <Header.Content>
              <Translate>Number of events</Translate>
              <Header.Subheader>
                <Translate>The year is the one of the start date of the event.</Translate>
              </Header.Subheader>
            </Header.Content>
          </Header>
          <Segment basic>
            {eventGraph[0].data.length === 0 ? (
              <Message info>
                <Translate>No data available</Translate>
              </Message>
            ) : (
              <div styleName="chart-container">
                <Chart
                  styleName="chart"
                  data={eventGraph}
                  series={series}
                  axes={axes}
                  tooltip={tooltip}
                />
              </div>
            )}
          </Segment>
        </Segment>
        <Segment>
          <Header as="h2">
            <Header.Content>
              <Translate>Number of contributions</Translate>
              <Header.Subheader>
                <Translate>The year is the one of the start date of the contribution.</Translate>
              </Header.Subheader>
            </Header.Content>
          </Header>
          <Segment basic>
            {contributionsGraph[0].data.length === 0 ? (
              <Message info>
                <Translate>No data available</Translate>
              </Message>
            ) : (
              <div styleName="chart-container">
                <Chart
                  styleName="chart"
                  data={contributionsGraph}
                  series={series}
                  axes={axes}
                  tooltip={tooltip}
                />
              </div>
            )}
          </Segment>
        </Segment>
      </Segment.Group>
      <Segment.Group horizontal>
        <Segment inverted color="blue" textAlign="center">
          <Statistic inverted>
            <Statistic.Value>{totalEvents}</Statistic.Value>
            <Statistic.Label>
              <Translate>Total number of events</Translate>
            </Statistic.Label>
          </Statistic>
        </Segment>
        <Segment inverted color="blue" textAlign="center">
          <Statistic inverted>
            <Statistic.Value>{totalContributions}</Statistic.Value>
            <Statistic.Label>
              <Translate>Total number of contributions</Translate>
            </Statistic.Label>
          </Statistic>
        </Segment>
        <Segment inverted color="blue" textAlign="center">
          <Statistic inverted>
            <Statistic.Value>{files}</Statistic.Value>
            <Statistic.Label>
              <Translate>Number of attachments</Translate>
            </Statistic.Label>
          </Statistic>
        </Segment>
        {data.users !== undefined && (
          <Segment inverted color="blue" textAlign="center">
            <Statistic inverted>
              <Statistic.Value>{users}</Statistic.Value>
              <Statistic.Label>
                <Translate>Number of users</Translate>
              </Statistic.Label>
            </Statistic>
          </Segment>
        )}
      </Segment.Group>
      <Translate>
        Last updated on: <Param name="time" value={updatedTime} />
      </Translate>
    </Container>
  );
}

CategoryStatisticsDisplay.propTypes = {
  data: PropTypes.shape({
    contributions: PropTypes.object.isRequired,
    events: PropTypes.object.isRequired,
    files: PropTypes.number.isRequired,
    updated: PropTypes.string.isRequired,
    users: PropTypes.number,
    totalEvents: PropTypes.number.isRequired,
    totalContributions: PropTypes.number.isRequired,
    minYear: PropTypes.number.isRequired,
    maxYear: PropTypes.number.isRequired,
  }).isRequired,
};
