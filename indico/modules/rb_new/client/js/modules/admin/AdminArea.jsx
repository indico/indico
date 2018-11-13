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
import PropTypes from 'prop-types';
import {Route} from 'react-router-dom';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Container, Grid, Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {selectors as userSelectors} from '../../common/user';
import AdminMenu from './AdminMenu';
import AdminLocationRooms from './AdminLocationRooms';
import * as adminSelectors from './selectors';
import * as adminActions from './actions';

import './AdminArea.module.scss';


class AdminArea extends React.Component {
    static propTypes = {
        locations: PropTypes.array.isRequired,
        isAdmin: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchLocations: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchLocations}} = this.props;
        fetchLocations();
    }

    render() {
        const {isAdmin} = this.props;
        const {locations} = this.props;

        if (!isAdmin) {
            return null;
        }

        const missingLocationsMessage = (
            <Message info>
                <Translate>
                    There are no locations defined.
                </Translate>
            </Message>
        );

        return (
            <Container styleName="admin-area">
                <Grid columns={2}>
                    <Grid.Column width={4} floated="left">
                        <AdminMenu />
                    </Grid.Column>
                    <Grid.Column width={12}>
                        <Route exact path="/admin"
                               render={() => <Translate>General settings</Translate>} />
                        <Route exact path="/admin/equipment-types"
                               render={() => <Translate>Equipment Types</Translate>} />
                        <Route path="/admin/location/:locationId"
                               render={({match: {params: {locationId}}}) => {
                                   if (locations.length) {
                                       return <AdminLocationRooms locationId={parseInt(locationId, 10)} />;
                                   } else {
                                       return missingLocationsMessage;
                                   }
                               }} />
                    </Grid.Column>
                </Grid>
            </Container>
        );
    }
}

export default connect(
    state => ({
        locations: adminSelectors.getAllLocations(state),
        isAdmin: userSelectors.isUserAdmin(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchLocations: adminActions.fetchLocations,
        }, dispatch),
    })
)(AdminArea);
