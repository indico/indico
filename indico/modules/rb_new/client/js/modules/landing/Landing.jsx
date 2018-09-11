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
import {Checkbox, Form, Grid} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import * as globalActions from '../../actions';
import BookingBootstrapForm from '../../components/BookingBootstrapForm';
import {parseSearchBarText} from '../../util';
import LandingStatistics from './LandingStatistics';

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
        onlyFavorites: false
    };

    disabledDate = (current) => {
        if (current) {
            return current.isBefore(moment(), 'day');
        }
    };

    doSearch = (formState) => {
        const {onlyFavorites, text} = this.state;
        const {actions: {setFilters}} = this.props;
        const parsed = parseSearchBarText(text);

        setFilters({
            ...formState,
            ...parsed,
            onlyFavorites,
            equipment: []
        });
    };

    updateText = (text) => {
        this.setState({text});
    };

    toggleFavorites = (_, {checked}) => {
        this.setState({onlyFavorites: checked});
    };

    render() {
        const {userHasFavorites} = this.props;
        return (
            <div className="landing-wrapper">
                <Grid centered styleName="landing-page">
                    <Grid.Row columns={2} styleName="landing-page-form">
                        <Grid.Column width={6} textAlign="center" verticalAlign="middle">
                            <div>
                                <BookingBootstrapForm onSearch={this.doSearch}>
                                    <Form.Group inline>
                                        <Form.Input placeholder="bldg: 28" styleName="search-input"
                                                    onChange={(event, data) => this.updateText(data.value)} />
                                    </Form.Group>
                                    {userHasFavorites && (
                                        <Form.Field>
                                            <Checkbox label={Translate.string('Search only my favourites')}
                                                      onClick={this.toggleFavorites} />
                                        </Form.Field>
                                    )}
                                </BookingBootstrapForm>
                            </div>
                        </Grid.Column>
                    </Grid.Row>
                    <Grid.Row>
                        <div styleName="statistics">
                            <LandingStatistics />
                        </div>
                    </Grid.Row>
                </Grid>
            </div>
        );
    }
}


export default connect(
    state => ({
        userHasFavorites: Object.keys(state.user.favorites).length > 0
    }),
    dispatch => ({
        actions: {
            setFilters(data) {
                dispatch(globalActions.setFilters('bookRoom', data));
            }
        }
    })
)(Landing);
