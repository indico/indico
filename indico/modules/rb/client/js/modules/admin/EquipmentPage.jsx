// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Grid} from 'semantic-ui-react';
import * as adminActions from './actions';
import RoomFeatureList from './RoomFeatureList';
import EquipmentTypeList from './EquipmentTypeList';


class EquipmentPage extends React.PureComponent {
    static propTypes = {
        actions: PropTypes.exact({
            fetchEquipmentTypes: PropTypes.func.isRequired,
            fetchFeatures: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchEquipmentTypes, fetchFeatures}} = this.props;
        fetchEquipmentTypes();
        fetchFeatures();
    }

    render() {
        return (
            <Grid columns={2}>
                <Grid.Column width={8}>
                    <EquipmentTypeList />
                </Grid.Column>
                <Grid.Column>
                    <RoomFeatureList />
                </Grid.Column>
            </Grid>
        );
    }
}

export default connect(
    null,
    dispatch => ({
        actions: bindActionCreators({
            fetchEquipmentTypes: adminActions.fetchEquipmentTypes,
            fetchFeatures: adminActions.fetchFeatures,
        }, dispatch),
    })
)(EquipmentPage);
