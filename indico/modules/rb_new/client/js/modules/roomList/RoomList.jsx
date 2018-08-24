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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Button, Card, Dimmer, Dropdown, Grid, Loader, Popup, Sticky} from 'semantic-ui-react';
import {Route} from 'react-router-dom';
import LazyScroll from 'redux-lazy-scroll';
import {stateToQueryString} from 'redux-router-querystring';

import {Slot} from 'indico/react/util';
import {Param, Plural, PluralTranslate, Translate, Singular} from 'indico/react/i18n';
import {pushStateMergeProps, roomPreloader} from '../../util';
import RoomFilterBar from '../../components/RoomFilterBar';
import filterBarFactory from '../../containers/FilterBar';
import searchBarFactory from '../../containers/SearchBar';
import mapControllerFactory from '../../containers/MapController';
import Room from '../../containers/Room';
import roomDetailsModalFactory from '../../components/modals/RoomDetailsModal';
import BookFromListModal from '../../components/modals/BookFromListModal';
import {BlockingModal} from '../blockings';
import {queryString as queryStringSerializer} from '../../serializers/filters';
import * as actions from '../../actions';
import * as selectors from '../../selectors';
import {actions as roomsActions, selectors as roomsSelectors} from '../../common/rooms';

import './RoomList.module.scss';


const FilterBar = filterBarFactory('roomList', RoomFilterBar);
const SearchBar = searchBarFactory('roomList');
const MapController = mapControllerFactory('roomList');
const RoomDetailsModal = roomDetailsModalFactory('roomList');


class RoomList extends React.Component {
    static propTypes = {
        rooms: PropTypes.shape({
            list: PropTypes.array,
            isFetching: PropTypes.bool,
        }).isRequired,
        roomDetailsFetching: PropTypes.bool.isRequired,
        pushState: PropTypes.func.isRequired,
        showMap: PropTypes.bool.isRequired,
        isInitializing: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchRooms: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
        }).isRequired,
    };

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {
        blockingMode: false,
        blockings: {}
    };

    componentDidMount() {
        const {actions: {fetchRooms}} = this.props;
        fetchRooms();
    }

    renderRoom = (room) => {
        const {id} = room;
        const {pushState} = this.props;
        const {blockingMode, blockings} = this.state;

        const showDetailsBtn = (
            <Button icon="search"
                    onClick={() => {
                        pushState(`/rooms/${id}/details`);
                    }}
                    primary
                    circular />
        );

        // TODO: rename this to something like "selectionMode"
        if (blockingMode) {
            const isRoomBlocked = room.id in blockings;
            const buttonProps = {compact: true, size: 'tiny'};

            if (!isRoomBlocked) {
                buttonProps.icon = 'check';
            } else {
                buttonProps.icon = 'remove';
                buttonProps.negative = true;
            }

            return (
                <Room key={room.id} room={room}>
                    <Slot>
                        <Button styleName="blocking-add-btn"
                                onClick={() => {
                                    if (room.id in blockings) {
                                        const newBlockings = {...blockings};
                                        delete newBlockings[room.id];
                                        this.setState({blockings: newBlockings});
                                    } else {
                                        this.setState({blockings: {...blockings, [room.id]: room}});
                                    }
                                }}
                                {...buttonProps} />
                    </Slot>
                </Room>
            );
        } else {
            return (
                <Room key={room.id} room={room} showFavoriteButton>
                    <Slot name="actions">
                        <Popup trigger={showDetailsBtn} content={Translate.string('Room details')} position="top center" />
                    </Slot>
                </Room>
            );
        }
    };

    closeBookingModal = () => {
        const {pushState} = this.props;
        pushState('/rooms', true);
    };

    closeBlockingModal = () => {
        const {pushState} = this.props;
        pushState('/rooms', true);
        this.setState({blockingMode: false, blockings: []});
    };

    toggleBlockingMode = () => {
        const {blockingMode} = this.state;
        this.setState({blockingMode: !blockingMode, blockings: []});
    };

    render() {
        const {
            rooms: {list, total, isFetching},
            actions: {fetchRooms, fetchRoomDetails},
            roomDetailsFetching,
            showMap,
            pushState,
            isInitializing,
        } = this.props;
        const {blockingMode, blockings} = this.state;
        const menuOptions = [{
            text: Translate.string('Block rooms'),
            value: 'block-rooms',
            onClick: this.toggleBlockingMode,
            icon: 'lock'
        }];

        return (
            <Grid columns={2}>
                <Grid.Column width={showMap ? 11 : 16}>
                    <div className="ui" styleName="room-list" ref={this.contextRef}>
                        <Sticky context={this.contextRef.current} className="sticky-filters">
                            <Grid>
                                <Grid.Column width={12}>
                                    <FilterBar />
                                </Grid.Column>
                                <Grid.Column width={4} textAlign="right" verticalAlign="middle">
                                    {blockingMode ? (
                                        <>
                                            <Button icon="check"
                                                    disabled={Object.keys(blockings).length === 0}
                                                    onClick={() => {
                                                        pushState('/rooms/blocking/create');
                                                    }}
                                                    primary
                                                    circular />
                                            <Button icon="cancel" onClick={this.toggleBlockingMode} circular />
                                        </>
                                    ) : (
                                        <Dropdown text={Translate.string('Actions')}
                                                  options={menuOptions}
                                                  direction="left"
                                                  button
                                                  floating />
                                    )}
                                </Grid.Column>
                            </Grid>
                            <SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />
                        </Sticky>
                        <div styleName="results-count">
                            {total === 0 && !isFetching && Translate.string('There are no rooms matching the criteria')}
                            {total !== 0 && (
                                <PluralTranslate count={total}>
                                    <Singular>
                                        There is <Param name="count" value={total} /> room matching the criteria
                                    </Singular>
                                    <Plural>
                                        There are <Param name="count" value={total} /> rooms matching the criteria
                                    </Plural>
                                </PluralTranslate>
                            )}
                        </div>
                        <LazyScroll hasMore={total > list.length} loadMore={() => fetchRooms(false)}
                                    isFetching={isFetching}>
                            <Card.Group stackable>
                                {list.map(this.renderRoom)}
                            </Card.Group>
                            <Loader active={isFetching} inline="centered" styleName="rooms-loader" />
                        </LazyScroll>
                    </div>
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetailsFetching} page>
                            <Loader />
                        </Dimmer>
                    </Dimmer.Dimmable>
                </Grid.Column>
                {showMap && (
                    <Grid.Column width={5}>
                        <MapController />
                    </Grid.Column>
                )}
                {!isInitializing && (
                    <>
                        <Route exact path="/rooms/:roomId/details" render={roomPreloader((roomId) => (
                            <RoomDetailsModal roomId={roomId} onClose={this.closeBookingModal} />
                        ), fetchRoomDetails)} />
                        <Route exact path="/rooms/:roomId/book" render={roomPreloader((roomId) => (
                            <BookFromListModal roomId={roomId} onClose={this.closeBookingModal} />
                        ), fetchRoomDetails)} />
                        <Route exact path="/rooms/blocking/create" render={() => (
                            <BlockingModal open
                                           rooms={Object.values(blockings)}
                                           onClose={this.closeBlockingModal} />
                        )} />
                    </>
                )}
            </Grid>
        );
    }
}


export default connect(
    state => ({
        ...state.roomList,
        roomDetailsFetching: roomsSelectors.isFetchingDetails(state),
        queryString: stateToQueryString(state.roomList, queryStringSerializer),
        showMap: selectors.isMapEnabled(state),
        isInitializing: selectors.isInitializing(state),
    }),
    dispatch => ({
        actions: {
            fetchRooms: (clear = true) => {
                dispatch(actions.searchRooms('roomList', clear));
                dispatch(actions.fetchMapRooms('roomList'));
            },
            fetchRoomDetails: bindActionCreators(roomsActions.fetchDetails, dispatch),
        },
        dispatch,
    }),
    pushStateMergeProps,
)(RoomList);
