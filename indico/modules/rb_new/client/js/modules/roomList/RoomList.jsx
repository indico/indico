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

import _ from 'lodash';
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
import camelizeKeys from 'indico/utils/camelize';
import {pushStateMergeProps, roomPreloader} from '../../util';
import roomFilterBarFactory from './RoomFilterBar';
import searchBarFactory from '../../containers/SearchBar';
import mapControllerFactory from '../../containers/MapController';
import Room from '../../containers/Room';
import roomDetailsModalFactory from '../../components/modals/RoomDetailsModal';
import BookFromListModal from '../../components/modals/BookFromListModal';
import {BlockingModal} from '../blockings';
import {queryString as queryStringSerializer} from '../../serializers/filters';
import {actions as roomsActions, selectors as roomsSelectors} from '../../common/rooms';
import * as selectors from '../../selectors';
import * as roomsListActions from './actions';
import * as roomsListSelectors from './selectors';

import './RoomList.module.scss';


const SearchBar = searchBarFactory('roomList');
const MapController = mapControllerFactory('roomList');
const RoomDetailsModal = roomDetailsModalFactory('roomList');
const RoomFilterBar = roomFilterBarFactory('roomList');

class RoomList extends React.Component {
    static propTypes = {
        filters: PropTypes.object.isRequired,
        results: PropTypes.arrayOf(PropTypes.object).isRequired,
        isSearching: PropTypes.bool.isRequired,
        roomDetailsFetching: PropTypes.bool.isRequired,
        showMap: PropTypes.bool.isRequired,
        isInitializing: PropTypes.bool.isRequired,
        pushState: PropTypes.func.isRequired,
        actions: PropTypes.exact({
            searchRooms: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
        }).isRequired,
    };

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {
        selectionMode: null,
        selection: {},
        numVisibleRooms: 20,
    };

    componentDidMount() {
        const {actions: {searchRooms}} = this.props;
        searchRooms();
    }

    componentDidUpdate({filters: prevFilters}) {
        const {filters, actions: {searchRooms}} = this.props;
        if (!_.isEqual(prevFilters, filters)) {
            searchRooms();
            // eslint-disable-next-line react/no-did-update-set-state
            this.setState({numVisibleRooms: 20});
        }
    }

    renderRoom = (room) => {
        const {id} = room;
        const {pushState} = this.props;
        const {selectionMode, selection} = this.state;

        const showDetailsBtn = (
            <Button icon="search"
                    onClick={() => {
                        pushState(`/rooms/${id}/details`);
                    }}
                    primary
                    circular />
        );

        if (selectionMode) {
            const isRoomSelected = room.id in selection;
            const buttonProps = {compact: true, size: 'tiny'};

            if (!isRoomSelected) {
                buttonProps.icon = 'check';
            } else {
                buttonProps.icon = 'check';
                buttonProps.primary = true;
            }

            return (
                <Room key={room.id} room={room}>
                    <Slot>
                        <Button styleName="selection-add-btn"
                                onClick={() => {
                                    if (room.id in selection) {
                                        const newSelection = {...selection};
                                        delete newSelection[room.id];
                                        this.setState({selection: newSelection});
                                    } else {
                                        this.setState({selection: {...selection, [room.id]: room}});
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
        this.clearSelectionMode();
    };

    clearSelectionMode = () => {
        this.setState({selectionMode: null, selection: []});
    };

    setSelectionMode = (type) => () => {
        this.setState({selectionMode: type, selection: []});
    };

    hasMoreRooms = () => {
        const {numVisibleRooms} = this.state;
        const {results} = this.props;
        return numVisibleRooms < results.length;
    };

    loadMoreRooms = () => {
        const {numVisibleRooms} = this.state;
        this.setState({numVisibleRooms: numVisibleRooms + 20});
    };

    get visibleRooms() {
        const {numVisibleRooms} = this.state;
        const {results} = this.props;
        return results.slice(0, numVisibleRooms);
    }

    render() {
        const {
            results,
            actions: {fetchRoomDetails},
            roomDetailsFetching,
            showMap,
            pushState,
            isInitializing,
            isSearching,
        } = this.props;
        const {selectionMode, selection} = this.state;
        const menuOptions = [{
            text: Translate.string('Block rooms'),
            value: 'block-rooms',
            onClick: this.setSelectionMode('blocking'),
            icon: 'lock'
        }];

        return (
            <Grid columns={2}>
                <Grid.Column computer={showMap ? 11 : 16} mobile={16}>
                    <div className="ui" styleName="room-list" ref={this.contextRef}>
                        <Sticky context={this.contextRef.current} className="sticky-filters">
                            <Grid>
                                <Grid.Column width={12}>
                                    <RoomFilterBar />
                                </Grid.Column>
                                <Grid.Column width={4} textAlign="right" verticalAlign="middle">
                                    {selectionMode ? (
                                        <>
                                            <Button icon="check"
                                                    disabled={Object.keys(selection).length === 0}
                                                    onClick={() => {
                                                        if (selectionMode === 'blocking') {
                                                            pushState('/rooms/blocking/create');
                                                        }
                                                    }}
                                                    primary
                                                    circular />
                                            <Button icon="cancel" onClick={this.clearSelectionMode} circular />
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
                            <SearchBar />
                        </Sticky>
                        <div styleName="results-count">
                            {results.length === 0 && !isSearching && Translate.string('There are no rooms matching the criteria')}
                            {results.length !== 0 && (
                                <PluralTranslate count={results.length}>
                                    <Singular>
                                        There is <Param name="count" value={results.length} /> room matching the criteria
                                    </Singular>
                                    <Plural>
                                        There are <Param name="count" value={results.length} /> rooms matching the criteria
                                    </Plural>
                                </PluralTranslate>
                            )}
                        </div>
                        {isSearching ? (
                            <Loader active inline="centered" styleName="rooms-loader" />
                        ) : (
                            <LazyScroll hasMore={this.hasMoreRooms()} loadMore={this.loadMoreRooms}>
                                <Card.Group stackable>
                                    {this.visibleRooms.map(this.renderRoom)}
                                </Card.Group>
                            </LazyScroll>
                        )}
                    </div>
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetailsFetching} page>
                            <Loader />
                        </Dimmer>
                    </Dimmer.Dimmable>
                </Grid.Column>
                {showMap && (
                    <Grid.Column computer={5} only="computer">
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
                        <Route exact path="/rooms/blocking/create" render={() => {
                            const blocking = {
                                blockedRooms: Object.values(selection).map((room) => ({room: camelizeKeys(room)}))
                            };

                            return (
                                <BlockingModal open
                                               blocking={blocking}
                                               onClose={this.closeBlockingModal} />
                            );
                        }} />
                    </>
                )}
            </Grid>
        );
    }
}


export default connect(
    state => ({
        filters: roomsListSelectors.getFilters(state),
        results: roomsListSelectors.getSearchResults(state),
        isSearching: roomsListSelectors.isSearching(state),
        roomDetailsFetching: roomsSelectors.isFetchingDetails(state),
        showMap: selectors.isMapReady(state),
        isInitializing: selectors.isInitializing(state),
        queryString: stateToQueryString(state.roomList, queryStringSerializer), // for pushStateMergeProps
    }),
    dispatch => ({
        dispatch, // for pushStateMergeProps
        actions: bindActionCreators({
            searchRooms: roomsListActions.searchRooms,
            fetchRoomDetails: roomsActions.fetchDetails,
        }, dispatch)
    }),
    pushStateMergeProps,
)(RoomList);
