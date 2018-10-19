/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import React from 'react';
import {connect} from 'react-redux';
import moment from 'moment';
import PropTypes from 'prop-types';
import {Card, Checkbox, Form, Grid} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';

import {actions as filtersActions} from '../../common/filters';
import BookingBootstrapForm from '../../components/BookingBootstrapForm';
import LandingStatistics from './LandingStatistics';
import {selectors as userSelectors} from '../../common/user';

import './Landing.module.scss';


class Landing extends React.Component {
    static propTypes = {
        actions: PropTypes.exact({
            setFilters: PropTypes.func.isRequired,
        }).isRequired,
        userHasFavorites: PropTypes.bool.isRequired
    };

    state = {
        text: null,
        extraState: {
            onlyFavorites: false
        }
    };

    disabledDate = (current) => {
        if (current) {
            return current.isBefore(moment(), 'day');
        }
    };

    doSearch = (formState) => {
        const {extraState, text} = this.state;
        const {actions: {setFilters}} = this.props;

        setFilters({
            ...formState,
            ...extraState,
            text,
            equipment: []
        });
    };

    updateText = (text) => {
        this.setState({text});
    };

    toggleFavorites = (_, {checked}) => {
        this.setExtraState({onlyFavorites: checked});
    };

    setExtraState = (attrs) => {
        const {extraState} = this.state;
        this.setState({extraState: {...extraState, ...attrs}});
    };

    render() {
        const {userHasFavorites} = this.props;
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
                                <Overridable id="BookingBootstrapForm">
                                    <BookingBootstrapForm onSearch={this.doSearch}>
                                        <Form.Group inline>
                                            <Form.Input placeholder="e.g. IT Amphitheatre" styleName="search-input"
                                                        onChange={(event, data) => this.updateText(data.value)} />
                                        </Form.Group>
                                        <Overridable id="Landing.bootstrapOptions"
                                                     setOptions={this.setExtraState}
                                                     options={extraState}>
                                            {userHasFavorites && (
                                                <Form.Field>
                                                    <Checkbox label={Translate.string('Search only my favourites')}
                                                              onClick={this.toggleFavorites} />
                                                </Form.Field>
                                            )}
                                        </Overridable>
                                    </BookingBootstrapForm>
                                </Overridable>
                            </Card.Content>
                        </Card>
                    </Grid.Row>
                    <Grid.Row styleName="landing-page-statistics">
                        <div styleName="statistics">
                            <Overridable id="LandingStatistics">
                                <LandingStatistics />
                            </Overridable>
                        </div>
                    </Grid.Row>
                </Grid>
            </div>
        );
    }
}


export default connect(
    state => ({
        userHasFavorites: userSelectors.hasFavoriteRooms(state)
    }),
    dispatch => ({
        actions: {
            setFilters(data) {
                dispatch(filtersActions.setFilters('bookRoom', data));
            }
        }
    })
)(Landing);
