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

import PropTypes from 'prop-types';
import React from 'react';
import {Grid, Icon, Message} from 'semantic-ui-react';
import _ from 'lodash';

import {Slot, toClasses} from 'indico/react/util';
import mapControllerFactory from '../../containers/MapController';
import RoomSearchPane from '../RoomSearchPane';
import BookingFilterBar from '../BookingFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBoxFactory from '../../containers/SearchBar';
import Room from '../Room';
import Timeline from '../../containers/Timeline';


import './BookRoom.module.scss';


const FilterBar = filterBarFactory('bookRoom', BookingFilterBar);
const SearchBar = searchBoxFactory('bookRoom');
const MapController = mapControllerFactory('bookRoom');


export default class BookRoom extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired,
        rooms: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
        }).isRequired,
        fetchRooms: PropTypes.func.isRequired,
        timeline: PropTypes.object.isRequired
    };

    constructor(props) {
        super(props);

        this.state = {
            view: 'book'
        };
    }

    componentWillUnmount() {
        const {setFilterParameter} = this.props;
        setFilterParameter('text', null);
    }

    renderRoom = (room) => {
        return (
            <Room key={room.id} room={room}>
                <Slot>
                    <Grid centered columns={3} style={{margin: 0, height: '100%', opacity: 0.9}}>
                        <Grid.Column verticalAlign="middle" width={14}>
                            <Message size="mini" warning compact>
                                <Message.Header>
                                    <Icon name="clock" /> 25 minutes later
                                </Message.Header>
                            </Message>
                        </Grid.Column>
                    </Grid>
                </Slot>
            </Room>
        );
    };

    renderMainContent = () => {
        const {view} = this.state;
        const {rooms, fetchRooms} = this.props;
        const filterBar = <FilterBar />;
        const searchBar = <SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />;

        if (view === 'book') {
            return (
                <RoomSearchPane rooms={rooms}
                                fetchRooms={fetchRooms}
                                filterBar={filterBar}
                                searchBar={searchBar}
                                renderRoom={this.renderRoom} />
            );
        } else if (view === 'timeline') {
            return (
                <>
                    {filterBar}
                    {searchBar}
                    <Timeline minHour={6} maxHour={22} />
                </>
            );
        }
    };

    switchToTimeline = () => {
        const {timeline: {availability}} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);

        if (timelineDataAvailable) {
            this.setState({view: 'timeline'});
        }
    };

    render() {
        const {view} = this.state;
        const {timeline: {availability}} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);
        const hasConflicts = Object.values(availability).some((data) => {
            return !_.isEmpty(data.conflicts);
        });

        return (
            <Grid columns={2}>
                <Grid.Column width={10}>
                    {this.renderMainContent()}
                </Grid.Column>
                <Grid.Column width={1} styleName="view-icons">
                    <span>
                        <Icon size="big" className={toClasses({active: view === 'book'})}
                              name="list" onClick={() => this.setState({view: 'book'})} />
                        <Icon.Group size="big" className={toClasses({active: view === 'timeline', disabled: !timelineDataAvailable})}
                                    onClick={this.switchToTimeline}>
                            <Icon name="calendar outline" disabled={!timelineDataAvailable} />
                            {hasConflicts && (
                                <Icon name="exclamation triangle" color="red" corner />
                            )}
                        </Icon.Group>
                    </span>
                </Grid.Column>
                <Grid.Column width={5}>
                    <MapController />
                </Grid.Column>
            </Grid>
        );
    }
}
