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
import PropTypes from 'prop-types';
import {Container, Grid, Item, Loader, Message} from 'semantic-ui-react';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {fetchBlockings} from '../../actions';
import BlockingFilterBar from '../BlockingFilterBar';
import filterBarFactory from '../../containers/FilterBar';

import './BlockingList.module.scss';


const FilterBar = filterBarFactory('blockingList', BlockingFilterBar);


class BlockingCard extends React.Component {
    static propTypes = {
        blocking: PropTypes.object.isRequired
    };

    renderCardHeader() {
        const {blocking} = this.props;
        const {blocked_rooms: blockedRooms} = blocking;

        if (blockedRooms.length === 1) {
            return blockedRooms[0].room.name;
        }

        return PluralTranslate.string('1 room', '{count} rooms', blockedRooms.length, {count: blockedRooms.length});
    }

    render() {
        const {blocking} = this.props;
        const {blocked_rooms: blockedRooms} = blocking;

        return (
            <Item.Group>
                <Item key={blocking.id}>
                    <Item.Image src={blockedRooms[0].room.large_photo_url} size="small" />
                    <Item.Content>
                        <Item.Header>{this.renderCardHeader()}</Item.Header>
                        <Item.Meta>
                            {blocking.start_date} - {blocking.end_date}
                        </Item.Meta>
                        <Item.Description>
                            {blocking.reason}
                        </Item.Description>
                    </Item.Content>
                </Item>
            </Item.Group>
        );
    }
}


class BlockingList extends React.Component {
    static propTypes = {
        list: PropTypes.array.isRequired,
        isFetching: PropTypes.bool.isRequired,
        fetchBlockings: PropTypes.func.isRequired
    };

    componentDidMount() {
        this.props.fetchBlockings(); // eslint-disable-line react/destructuring-assignment
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
                    <FilterBar />
                    {blockings.length ? (
                        <>
                            <Grid columns={4} styleName="blockings-list" stackable>
                                {blockings.map(this.renderBlocking)}
                            </Grid>
                            <Loader active={isFetching} inline="centered" />
                        </>
                    ) : (
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

const mapStateToProps = ({blockingList: {blockings}}) => ({...blockings});

const mapDispatchToProps = dispatch => ({
    fetchBlockings: () => {
        dispatch(fetchBlockings());
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(BlockingList);
