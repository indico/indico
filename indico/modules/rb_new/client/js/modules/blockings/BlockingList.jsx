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
import {Card, Container, Message, Sticky} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {ScrollButton} from 'indico/react/components';

import BlockingCard from './BlockingCard';
import CardPlaceholder from '../../components/CardPlaceholder';
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

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {
        scrollBtnVisible: false,
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
            <BlockingCard key={blocking.id}
                          blocking={blocking}
                          onClick={() => openBlockingDetails(blocking.id)} />
        );
    };

    renderContent = () => {
        const {isFetching, blockings} = this.props;
        const blockingsList = Object.values(blockings);

        if (isFetching) {
            return <CardPlaceholder.Group count={10} className="blockings-placeholders" />;
        } else if (blockingsList.length !== 0) {
            return (
                <Card.Group styleName="blockings-list" stackable>
                    {blockingsList.map(this.renderBlocking)}
                </Card.Group>
            );
        } else {
            return (
                <Message info>
                    <Translate>
                        There are no blockings.
                    </Translate>
                </Message>
            );
        }
    };

    render() {
        const {scrollBtnVisible} = this.state;
        return (
            <div ref={this.contextRef}>
                <Container styleName="blockings-container" fluid>
                    <Sticky context={this.contextRef.current} className="sticky-filters"
                            onStick={() => this.setState({scrollBtnVisible: true})}
                            onUnstick={() => this.setState({scrollBtnVisible: false})}>
                        <BlockingFilterBar />
                        <ScrollButton visible={scrollBtnVisible} />
                    </Sticky>
                    {this.renderContent()}
                </Container>
            </div>
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
