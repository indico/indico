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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Container, Grid, Loader, Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import BlockingCard from './BlockingCard';
import BlockingFilterBar from './BlockingFilterBar';
import * as blockingsActions from './actions';
import * as blockingsSelectors from './selectors';

import './BlockingList.module.scss';


class BlockingList extends React.Component {
    static propTypes = {
        blockings: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        filters: PropTypes.object.isRequired,
        actions: PropTypes.exact({
            fetchBlockings: PropTypes.func.isRequired,
            openBlockingDetails: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchBlockings}} = this.props;
        fetchBlockings();
    }

    componentDidUpdate({filters: prevFilters}) {
        const {filters, actions: {fetchBlockings}} = this.props;
        if (prevFilters !== filters) {
            fetchBlockings();
        }
    }

    renderBlocking = (blocking) => {
        const {actions: {openBlockingDetails}} = this.props;
        return (
            <Grid.Column key={blocking.id}>
                <BlockingCard blocking={blocking} onClick={() => openBlockingDetails(blocking.id)} />
            </Grid.Column>
        );
    };

    render() {
        const {blockings, isFetching} = this.props;
        const blockingsList = Object.values(blockings);
        return (
            <>
                <Container styleName="blockings-container">
                    <BlockingFilterBar />
                    {!isFetching && blockingsList.length !== 0 && (
                        <>
                            <Grid columns={4} styleName="blockings-list" stackable>
                                {blockingsList.map(this.renderBlocking)}
                            </Grid>
                        </>
                    )}
                    {isFetching && <Loader inline="centered" active />}
                    {!isFetching && blockingsList.length === 0 && (
                        <Message info>
                            <Translate>
                                There are no blockings.
                            </Translate>
                        </Message>
                    )}
                </Container>
            </>
        );
    }
}


export default connect(
    state => ({
        blockings: blockingsSelectors.getAllBlockings(state),
        isFetching: blockingsSelectors.isFetchingBlockings(state),
        filters: blockingsSelectors.getFilters(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchBlockings: blockingsActions.fetchBlockings,
            openBlockingDetails: blockingsActions.openBlockingDetails,
        }, dispatch),
    })
)(BlockingList);
