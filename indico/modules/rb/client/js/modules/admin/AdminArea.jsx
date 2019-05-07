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
import {Container, Grid} from 'semantic-ui-react';
import {selectors as userSelectors} from '../../common/user';
import AdminMenu from './AdminMenu';
import AdminLocationRooms from './AdminLocationRooms';
import EquipmentPage from './EquipmentPage';
import AttributesPage from './AttributesPage';
import LocationPage from './LocationPage';
import SettingsPage from './SettingsPage';
import * as adminActions from './actions';

import './AdminArea.module.scss';


class AdminArea extends React.Component {
    static propTypes = {
        isAdmin: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchLocations: PropTypes.func.isRequired,
            fetchRooms: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchLocations, fetchRooms}} = this.props;
        fetchLocations();
        fetchRooms();
    }

    render() {
        const {isAdmin} = this.props;

        if (!isAdmin) {
            return null;
        }

        return (
            <Container styleName="admin-area">
                <Grid columns={2}>
                    <Grid.Column width={4} floated="left">
                        <AdminMenu />
                    </Grid.Column>
                    <Grid.Column width={12}>
                        <Route exact path="/admin" component={SettingsPage} />
                        <Route exact path="/admin/equipment" component={EquipmentPage} />
                        <Route exact path="/admin/attributes" component={AttributesPage} />
                        <Route exact path="/admin/locations/" component={LocationPage} />
                        <Route exact path="/admin/locations/:locationId"
                               render={({match: {params: {locationId}}}) => (
                                   <AdminLocationRooms locationId={parseInt(locationId, 10)} />
                               )} />
                    </Grid.Column>
                </Grid>
            </Container>
        );
    }
}

export default connect(
    state => ({
        isAdmin: userSelectors.isUserRBAdmin(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchLocations: adminActions.fetchLocations,
            fetchRooms: adminActions.fetchRooms,
        }, dispatch),
    })
)(AdminArea);
