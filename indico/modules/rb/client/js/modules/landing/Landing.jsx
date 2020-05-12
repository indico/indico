// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import Overridable from 'react-overridable';
import {Card, Checkbox, Form, Grid} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {Carousel} from 'indico/react/components';
import {Responsive} from 'indico/react/util';
import {toMoment} from 'indico/utils/date';

import {actions as filtersActions} from '../../common/filters';
import BookingBootstrapForm from '../../components/BookingBootstrapForm';
import LandingStatistics from './LandingStatistics';
import UpcomingBookings from './UpcomingBookings';
import {selectors as userSelectors} from '../../common/user';
import {selectors as bookRoomSelectors} from '../bookRoom';
import * as landingActions from './actions';
import * as landingSelectors from './selectors';

import './Landing.module.scss';

export class Landing extends React.Component {
  static propTypes = {
    actions: PropTypes.exact({
      setFilters: PropTypes.func.isRequired,
      fetchUpcomingBookings: PropTypes.func.isRequired,
    }).isRequired,
    userHasFavorites: PropTypes.bool.isRequired,
    showUpcomingBookings: PropTypes.bool,
    fetchedUpcomingBookings: PropTypes.bool.isRequired,
    hasUpcomingBookings: PropTypes.bool.isRequired,
    upcomingBookings: PropTypes.arrayOf(PropTypes.object),
    filters: PropTypes.shape({
      text: PropTypes.string,
      dates: PropTypes.shape({
        startDate: PropTypes.string,
        endDate: PropTypes.string,
      }).isRequired,
    }).isRequired,
  };

  static defaultProps = {
    upcomingBookings: null,
    showUpcomingBookings: true,
  };

  state = {
    text: null,
    extraState: {
      onlyFavorites: false,
    },
  };

  componentDidMount() {
    const {
      actions: {fetchUpcomingBookings},
      showUpcomingBookings,
      filters: {text},
    } = this.props;
    if (showUpcomingBookings) {
      fetchUpcomingBookings();
    }
    if (text) {
      this.updateText(text);
    }
  }

  doSearch = formState => {
    const {extraState, text} = this.state;
    const {
      actions: {setFilters},
    } = this.props;

    setFilters({
      ...formState,
      ...extraState,
      text,
      equipment: [],
    });
  };

  updateText = text => {
    this.setState({text});
  };

  toggleFavorites = (_, {checked}) => {
    this.setExtraState({onlyFavorites: checked});
  };

  setExtraState = attrs => {
    const {extraState} = this.state;
    this.setState({extraState: {...extraState, ...attrs}});
  };

  renderCarousel() {
    const {upcomingBookings} = this.props;
    const panes = [
      {key: 'upcoming', content: <UpcomingBookings bookings={upcomingBookings} />, delay: 20},
      {key: 'stats', content: <LandingStatistics />},
    ];
    return <Carousel panes={panes} />;
  }

  render() {
    const {
      userHasFavorites,
      showUpcomingBookings,
      hasUpcomingBookings,
      fetchedUpcomingBookings,
      filters: {
        dates: {startDate},
      },
    } = this.props;
    const {extraState, text} = this.state;
    const defaults = startDate
      ? {dates: {startDate: toMoment(startDate, moment.HTML5_FMT.DATE)}}
      : {};
    return (
      <div className="landing-wrapper">
        <Grid centered styleName="landing-page" columns={1}>
          <Grid.Row styleName="landing-page-form">
            <Card styleName="landing-page-card">
              <Card.Content>
                <Card.Header>
                  <Translate>Start your booking...</Translate>
                </Card.Header>
              </Card.Content>
              <Card.Content styleName="landing-page-card-content">
                <BookingBootstrapForm onSearch={this.doSearch} defaults={defaults}>
                  <Form.Group inline>
                    <Form.Input
                      placeholder="e.g. IT Amphitheatre"
                      styleName="search-input"
                      onChange={(event, data) => this.updateText(data.value)}
                      value={text || ''}
                    />
                  </Form.Group>
                  <Overridable
                    id="Landing.bootstrapOptions"
                    setOptions={this.setExtraState}
                    options={extraState}
                  >
                    {userHasFavorites && (
                      <Form.Field>
                        <Checkbox
                          label={Translate.string('Search only my favourites')}
                          onClick={this.toggleFavorites}
                        />
                      </Form.Field>
                    )}
                  </Overridable>
                </BookingBootstrapForm>
              </Card.Content>
            </Card>
          </Grid.Row>
          <Responsive.Desktop andLarger minDeviceHeigth={900}>
            {(!showUpcomingBookings || fetchedUpcomingBookings) && (
              <Grid.Row styleName="landing-page-lower-row">
                <div styleName="lower-row">
                  {hasUpcomingBookings ? this.renderCarousel() : <LandingStatistics />}
                </div>
              </Grid.Row>
            )}
          </Responsive.Desktop>
        </Grid>
      </div>
    );
  }
}

export default connect(
  state => ({
    userHasFavorites: userSelectors.hasFavoriteRooms(state),
    fetchedUpcomingBookings: landingSelectors.hasFetchedUpcomingBookings(state),
    hasUpcomingBookings: landingSelectors.hasUpcomingBookings(state),
    upcomingBookings: landingSelectors.getUpcomingBookings(state),
    filters: bookRoomSelectors.getFilters(state),
  }),
  dispatch => ({
    actions: {
      setFilters(data) {
        dispatch(filtersActions.setFilters('bookRoom', data));
      },
      fetchUpcomingBookings() {
        dispatch(landingActions.fetchUpcomingBookings());
      },
    },
  })
)(Overridable.component('Landing', Landing));
