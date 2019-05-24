// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
import MapAreasPage from './MapAreasPage';
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
                        <Route exact path="/admin/map-areas" component={MapAreasPage} />
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
