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
import {Button, Card, Dropdown, Grid, Loader, Popup, Sticky} from 'semantic-ui-react';
import {Route} from 'react-router-dom';
import LazyScroll from 'redux-lazy-scroll';
import {stateToQueryString} from 'redux-router-querystring';

import {Slot} from 'indico/react/util';
import {Param, Plural, PluralTranslate, Translate, Singular} from 'indico/react/i18n';
import camelizeKeys from 'indico/utils/camelize';
import {pushStateMergeProps} from '../../util';
import roomFilterBarFactory from './RoomFilterBar';
import searchBarFactory from '../../components/SearchBar';
import Room from '../../containers/Room';
import {BlockingModal} from '../blockings';
import {queryStringRules as queryStringSerializer} from '../../common/roomSearch';
import {mapControllerFactory, selectors as mapSelectors} from '../../common/map';
import {actions as roomsActions} from '../../common/rooms';
import * as roomsListActions from './actions';
import * as roomsListSelectors from './selectors';

import './RoomList.module.scss';


const SearchBar = searchBarFactory('roomList', roomsListSelectors);
const MapController = mapControllerFactory('roomList', roomsListSelectors);
const RoomFilterBar = roomFilterBarFactory('roomList');

class RoomList extends React.Component {
    static propTypes = {
        filters: PropTypes.object.isRequired,
        results: PropTypes.arrayOf(PropTypes.object).isRequired,
        isSearching: PropTypes.bool.isRequired,
        showMap: PropTypes.bool.isRequired,
        pushState: PropTypes.func.isRequired,
        actions: PropTypes.exact({
            searchRooms: PropTypes.func.isRequired,
            openRoomDetails: PropTypes.func.isRequired,
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
        const {actions: {openRoomDetails}} = this.props;
        const {selectionMode, selection} = this.state;

        const showDetailsBtn = (
            <Button icon="search"
                    onClick={() => openRoomDetails(id)}
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
            showMap,
            pushState,
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
                            <div className="filter-row">
                                <div className="filter-row-filters">
                                    <RoomFilterBar />
                                    <SearchBar />
                                </div>
                                <div styleName="actions">
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
                                                  className="large"
                                                  options={menuOptions}
                                                  direction="left"
                                                  button
                                                  floating />
                                    )}
                                </div>
                            </div>
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
                </Grid.Column>
                {showMap && (
                    <Grid.Column computer={5} only="computer">
                        <MapController />
                    </Grid.Column>
                )}
                <Route exact path="/rooms/blocking/create" render={() => {
                    const blocking = {
                        blockedRooms: Object.values(selection).map((room) => ({room: camelizeKeys(room)}))
                    };

                    return (
                        <BlockingModal mode="create" blocking={blocking} onClose={this.closeBlockingModal} />
                    );
                }} />
            </Grid>
        );
    }
}


export default connect(
    state => ({
        filters: roomsListSelectors.getFilters(state),
        results: roomsListSelectors.getSearchResults(state),
        isSearching: roomsListSelectors.isSearching(state),
        showMap: mapSelectors.isMapVisible(state),
        queryString: stateToQueryString(state.roomList, queryStringSerializer), // for pushStateMergeProps
    }),
    dispatch => ({
        dispatch, // for pushStateMergeProps
        actions: bindActionCreators({
            searchRooms: roomsListActions.searchRooms,
            openRoomDetails: roomsActions.openRoomDetails,
        }, dispatch)
    }),
    pushStateMergeProps,
)(RoomList);
