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
import BlockingFilterBar from './BlockingFilterBar';
import BlockingCard from './BlockingCard';
import * as blockingsActions from './actions';
import * as blockingsSelectors from './selectors';

import './BlockingList.module.scss';


class BlockingList extends React.Component {
    static propTypes = {
        list: PropTypes.array.isRequired,
        isFetching: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchBlockings: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchBlockings}} = this.props;
        fetchBlockings();
    }

    renderBlocking = (blocking) => {
        return (
            <Grid.Column key={blocking.id}>
                <BlockingCard blocking={blocking} />
            </Grid.Column>
        );
    };

    render() {
        const {list: blockings, isFetching} = this.props;
        return (
            <>
                <Container styleName="blockings-container">
                    <BlockingFilterBar />
                    {!isFetching && blockings.length !== 0 && (
                        <>
                            <Grid columns={4} styleName="blockings-list" stackable>
                                {blockings.map(this.renderBlocking)}
                            </Grid>
                        </>
                    )}
                    {isFetching && <Loader inline="centered" active />}
                    {!isFetching && blockings.length === 0 && (
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
        list: blockingsSelectors.getAllBlockings(state),
        isFetching: blockingsSelectors.isFetchingBlockings(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchBlockings: blockingsActions.fetchBlockings,
        }, dispatch),
    })
)(BlockingList);
