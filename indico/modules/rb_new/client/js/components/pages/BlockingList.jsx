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
import {Container, Card, Image, Loader} from 'semantic-ui-react';
import {Param, PluralTranslate, Plural, Singular} from 'indico/react/i18n';
import {fetchBlockings} from '../../actions';

import './BlockingList.module.scss';


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
        const numberOfBlockedRooms = blocking.blocked_rooms.length;
        return (
            <Card key={blocking.id}>
                <Image key={blocking.blocked_rooms[0].room.id}
                       src={blocking.blocked_rooms[0].room.large_photo_url}
                       size="medium" />
                <Card.Content>
                    <Card.Header>
                        <PluralTranslate count={numberOfBlockedRooms}>
                            <Singular>
                                1 room
                            </Singular>
                            <Plural>
                                <Param name="count" value={numberOfBlockedRooms} /> rooms
                            </Plural>
                        </PluralTranslate>
                    </Card.Header>
                    <Card.Meta>
                        {blocking.start_date} - {blocking.end_date}
                    </Card.Meta>
                    <Card.Description>
                        {blocking.reason}
                    </Card.Description>
                </Card.Content>
            </Card>
        );
    };

    render() {
        const {list: blockings, isFetching} = this.props;
        return (
            <>
                <Container styleName="blockings-list" fluid>
                    <Card.Group stackable>
                        {blockings.map(this.renderBlocking)}
                    </Card.Group>
                    <Loader active={isFetching} inline="centered" />
                </Container>
            </>
        );
    }
}

const mapStateToProps = ({blockings}) => ({...blockings});

const mapDispatchToProps = dispatch => ({
    fetchBlockings: () => {
        dispatch(fetchBlockings());
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(BlockingList);
