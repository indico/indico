// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Card, Checkbox, Form, Grid} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {Carousel} from 'indico/react/components';
import {Overridable} from 'indico/react/util';

import {actions as filtersActions} from '../../common/filters';
import BookingBootstrapForm from '../../components/BookingBootstrapForm';
import LandingStatistics from './LandingStatistics';
import UpcomingBookings from './UpcomingBookings';
import {selectors as userSelectors} from '../../common/user';
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
    } = this.props;
    if (showUpcomingBookings) {
      fetchUpcomingBookings();
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
    } = this.props;
    const {extraState} = this.state;
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
                <BookingBootstrapForm onSearch={this.doSearch}>
                  <Form.Group inline>
                    <Form.Input
                      placeholder="e.g. IT Amphitheatre"
                      styleName="search-input"
                      onChange={(event, data) => this.updateText(data.value)}
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
          {(!showUpcomingBookings || fetchedUpcomingBookings) && (
            <Grid.Row styleName="landing-page-lower-row">
              <div styleName="lower-row">
                {hasUpcomingBookings ? this.renderCarousel() : <LandingStatistics />}
              </div>
            </Grid.Row>
          )}
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
