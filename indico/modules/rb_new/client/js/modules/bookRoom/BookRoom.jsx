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

import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';
import {Route} from 'react-router-dom';
import {Button, Card, Dimmer, Grid, Header, Icon, Label, Loader, Message, Popup, Sticky} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';

import {Slot, toClasses} from 'indico/react/util';
import {PluralTranslate, Translate, Singular, Param, Plural} from 'indico/react/i18n';
import {serializeTime} from 'indico/utils/date';
import mapControllerFactory from '../../containers/MapController';
import searchBoxFactory from '../../containers/SearchBar';
import Room from '../../containers/Room';
import BookingFilterBar from './BookingFilterBar';
import roomFilterBarFactory from '../../modules/roomList/RoomFilterBar';
import BookingTimeline from './BookingTimeline';
import BookRoomModal from './BookRoomModal';
import SearchResultCount from './SearchResultCount';
import roomDetailsModalFactory from '../../components/modals/RoomDetailsModal';
import {roomPreloader, pushStateMergeProps} from '../../util';
import {queryString as qsFilterRules} from '../../serializers/filters';
import {rules as qsBookRoomRules} from './queryString';

import * as bookRoomActions from './actions';
import * as globalActions from '../../actions';
import * as globalSelectors from '../../selectors';
import * as bookRoomSelectors from './selectors';
import {actions as roomsActions, selectors as roomsSelectors} from '../../common/rooms';

import './BookRoom.module.scss';


const SearchBar = searchBoxFactory('bookRoom');
const MapController = mapControllerFactory('bookRoom', bookRoomSelectors);
const RoomDetailsModal = roomDetailsModalFactory('bookRoom');
const RoomFilterBar = roomFilterBarFactory('bookRoom');

/* eslint-disable react/no-unused-state */
class BookRoom extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired,
        clearTextFilter: PropTypes.func.isRequired,
        results: PropTypes.arrayOf(PropTypes.object).isRequired,
        isInitializing: PropTypes.bool.isRequired,
        isSearching: PropTypes.bool.isRequired,
        isTimelineVisible: PropTypes.bool.isRequired,
        hasConflicts: PropTypes.bool.isRequired,
        totalResultCount: PropTypes.number.isRequired,
        searchRooms: PropTypes.func.isRequired,
        filters: PropTypes.object.isRequired,
        roomDetailsFetching: PropTypes.bool.isRequired,
        fetchRoomDetails: PropTypes.func.isRequired,
        fetchRoomSuggestions: PropTypes.func.isRequired,
        resetRoomSuggestions: PropTypes.func.isRequired,
        resetBookingAvailability: PropTypes.func.isRequired,
        suggestions: PropTypes.arrayOf(PropTypes.object).isRequired,
        pushState: PropTypes.func.isRequired,
        toggleTimelineView: PropTypes.func.isRequired,
        showMap: PropTypes.bool.isRequired
    };

    state = {
        maxVisibleRooms: 20,
        suggestionsRequested: false,
    };

    componentDidMount() {
        const {searchRooms} = this.props;
        searchRooms();
    }

    componentDidUpdate({filters: prevFilters}) {
        const {filters} = this.props;
        if (!_.isEqual(prevFilters, filters)) {
            this.restartSearch();
        }
    }

    componentWillUnmount() {
        const {clearTextFilter} = this.props;
        clearTextFilter();
    }

    restartSearch() {
        const {searchRooms, resetRoomSuggestions} = this.props;
        searchRooms();
        resetRoomSuggestions();
        this.setState({maxVisibleRooms: 20, suggestionsRequested: false});
    }

    renderRoom = (room) => {
        const {id} = room;
        const {pushState} = this.props;

        const bookingModalBtn = (
            <Button positive icon="check" circular onClick={() => {
                // open confirm dialog, keep same filtering parameters
                pushState(`/book/${id}/confirm`, true);
            }} />
        );
        const showDetailsBtn = (
            <Button primary icon="search" circular onClick={() => {
                pushState(`/book/${id}/details`, true);
            }} />
        );
        return (
            <Room key={room.id} room={room} showFavoriteButton>
                <Slot name="actions">
                    <Popup trigger={bookingModalBtn} content={Translate.string('Book room')} position="top center" hideOnScroll />
                    <Popup trigger={showDetailsBtn} content={Translate.string('Room details')} position="top center" hideOnScroll />
                </Slot>
            </Room>
        );
    };

    renderFilters(refName) {
        const {[refName]: ref} = this.state;
        return (
            <Sticky context={ref} className="sticky-filters">
                <div styleName="filter-row">
                    <div styleName="filter-row-filters">
                        <BookingFilterBar />
                        <RoomFilterBar />
                        <SearchBar />
                    </div>
                    {this.renderViewSwitch()}
                </div>
            </Sticky>
        );
    }

    hasMoreRooms = (allowSuggestions = true) => {
        const {maxVisibleRooms, suggestionsRequested} = this.state;
        const {results} = this.props;
        return maxVisibleRooms < results.length || (allowSuggestions && !suggestionsRequested);
    };

    loadMoreRooms = () => {
        const {fetchRoomSuggestions} = this.props;
        const {maxVisibleRooms} = this.state;
        if (this.hasMoreRooms(false)) {
            this.setState({maxVisibleRooms: maxVisibleRooms + 20});
        } else {
            this.setState({suggestionsRequested: true});
            fetchRoomSuggestions();
        }
    };

    get visibleRooms() {
        const {maxVisibleRooms} = this.state;
        const {results} = this.props;
        return results.slice(0, maxVisibleRooms);
    }

    get timelineButtonEnabled() {
        const {results, suggestions} = this.props;
        return !!(results.length || suggestions.length);
    }

    renderMainContent = () => {
        const {
            roomDetailsFetching,
            isSearching,
            totalResultCount,
            results,
            isTimelineVisible,
        } = this.props;

        if (!isTimelineVisible) {
            return (
                <>
                    <div className="ui" styleName="available-room-list" ref={ref => this.handleContextRef(ref, 'tileRef')}>
                        {this.renderFilters('tileRef')}
                        <SearchResultCount matching={results.length} total={totalResultCount}
                                           isFetching={isSearching} />
                        {!isSearching && (
                            <>
                                <LazyScroll hasMore={this.hasMoreRooms()} loadMore={this.loadMoreRooms}>
                                    <Card.Group stackable>
                                        {this.visibleRooms.map(this.renderRoom)}
                                    </Card.Group>
                                    <Loader active={isSearching} inline="centered" styleName="rooms-loader" />
                                </LazyScroll>
                                {this.renderSuggestions()}
                            </>
                        )}
                    </div>
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetailsFetching} page>
                            <Loader />
                        </Dimmer>
                    </Dimmer.Dimmable>
                </>
            );
        } else {
            return (
                <div styleName="available-room-list" ref={(ref) => this.handleContextRef(ref, 'timelineRef')}>
                    {this.renderFilters('timelineRef')}
                    <SearchResultCount matching={results.length} total={totalResultCount} isFetching={isSearching} />
                    <BookingTimeline minHour={6} maxHour={22} />
                </div>
            );
        }
    };

    renderSuggestions = () => {
        const {suggestions} = this.props;
        if (!suggestions.length) {
            return;
        }

        return (
            <>
                <Header as="h2">
                    <Translate>Rooms that you might be interested in</Translate>
                </Header>
                <Card.Group styleName="suggestions" stackable>
                    {suggestions.map((suggestion) => this.renderSuggestion(suggestion))}
                </Card.Group>
            </>
        );
    };

    renderSuggestion = ({room, suggestions}) => {
        return (
            <Room key={room.id} room={room}>
                <Slot>
                    <Grid centered styleName="suggestion" columns={3}>
                        <Grid.Column verticalAlign="middle" width={14}>
                            {this.renderSuggestionText(room, suggestions)}
                        </Grid.Column>
                    </Grid>
                </Slot>
            </Room>
        );
    };

    suggestionTooltip = (element) => (
        <Popup trigger={element} content={Translate.string('The filtering criteria will be adjusted accordingly')} />
    );

    renderSuggestionText = (room, {time, duration, skip}) => {
        const {pushState} = this.props;
        return (
            <>
                {time && this.suggestionTooltip(
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.updateFilters('time', time)}
                             warning compact>
                        <Message.Header>
                            <Icon name="clock" />
                            <PluralTranslate count={time}>
                                <Singular>
                                    One minute <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                </Singular>
                                <Plural>
                                    <Param name="count" value={Math.abs(time)} /> minutes{' '}
                                    <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                </Plural>
                            </PluralTranslate>
                        </Message.Header>
                    </Message>
                )}
                {duration && time && (
                    <div>
                        <Label color="brown" circular>{Translate.string('or')}</Label>
                    </div>
                )}
                {duration && this.suggestionTooltip(
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.updateFilters('duration', duration)}
                             warning compact>
                        <Message.Header>
                            <Icon name="hourglass full" /> {PluralTranslate.string('One minute shorter', '{duration} minutes shorter', duration, {duration})}
                        </Message.Header>
                    </Message>
                )}
                {skip && (
                    <Message styleName="suggestion-text" size="mini" onClick={() => {
                        pushState(`/book/${room.id}/confirm`, true);
                    }} warning compact>
                        <Message.Header>
                            <Icon name="calendar times" /> {PluralTranslate.string('Skip one day', 'Skip {skip} days', skip, {skip})}
                        </Message.Header>
                    </Message>
                )}
            </>
        );
    };

    updateFilters = (filter, value) => {
        const {setFilterParameter} = this.props;
        let {filters: {timeSlot: {startTime, endTime}}} = this.props;

        if (filter === 'duration') {
            endTime = serializeTime(moment(endTime, 'HH:mm').subtract(value, 'minutes'));
        } else if (filter === 'time') {
            startTime = serializeTime(moment(startTime, 'HH:mm').add(value, 'minutes'));
            endTime = serializeTime(moment(endTime, 'HH:mm').add(value, 'minutes'));
        }
        setFilterParameter('timeSlot', {startTime, endTime});
    };

    renderViewSwitch() {
        const {isTimelineVisible, hasConflicts} = this.props;
        const classes = toClasses({active: isTimelineVisible, disabled: !this.timelineButtonEnabled});

        const listBtn = (
            <Button icon={<Icon name="grid layout" styleName="switcher-icon" />}
                    className={toClasses({active: !isTimelineVisible})}
                    onClick={this.switchToRoomList} circular />
        );
        const timelineBtn = (
            <Button icon={<Icon name="calendar outline" styleName="switcher-icon"
                                disabled={!this.timelineButtonEnabled} />}
                    className={classes} circular />
        );
        return (
            <div styleName="view-icons">
                <span styleName="icons-wrapper">
                    {isTimelineVisible
                        ? <Popup trigger={listBtn} content={Translate.string('List view')} />
                        : listBtn
                    }
                    <Icon.Group onClick={this.switchToTimeline}>
                        {!isTimelineVisible
                            ? <Popup trigger={timelineBtn} content={Translate.string('Timeline view')} />
                            : timelineBtn
                        }
                        {hasConflicts && (
                            <Icon name="exclamation triangle" styleName="conflicts-icon" color="red" corner />
                        )}
                    </Icon.Group>
                </span>
            </div>
        );
    }

    switchToRoomList = () => {
        const {toggleTimelineView, isTimelineVisible} = this.props;
        if (isTimelineVisible) {
            toggleTimelineView(false);
            this.setState({timelineRef: null});
            this.restartSearch();
        }
    };

    switchToTimeline = () => {
        const {toggleTimelineView, isTimelineVisible} = this.props;
        if (!isTimelineVisible && this.timelineButtonEnabled) {
            toggleTimelineView(true);
            this.setState({tileRef: null});
        }
    };

    handleContextRef = (ref, kind) => {
        if (kind in this.state) {
            const {[kind]: context} = this.state;
            if (context !== null) {
                return;
            }
        }
        this.setState({[kind]: ref});
    };

    closeBookingModal = () => {
        const {resetBookingAvailability} = this.props;
        resetBookingAvailability();
        this.closeModal();
    };

    closeModal = () => {
        const {pushState} = this.props;
        pushState(`/book`, true);
    };

    render() {
        const {fetchRoomDetails, showMap, isInitializing} = this.props;
        return (
            <Grid columns={2}>
                <Grid.Column computer={showMap ? 11 : 16} mobile={16}>
                    {this.renderMainContent()}
                </Grid.Column>
                {showMap && (
                    <Grid.Column computer={5} only="computer">
                        <MapController />
                    </Grid.Column>
                )}
                {!isInitializing && (
                    <>
                        <Route exact path="/book/:roomId/confirm" render={roomPreloader((roomId) => (
                            <BookRoomModal open roomId={roomId} onClose={this.closeBookingModal} />
                        ), fetchRoomDetails)} />
                        <Route exact path="/book/:roomId/details" render={roomPreloader((roomId) => (
                            <RoomDetailsModal roomId={roomId} onClose={this.closeModal} />
                        ), fetchRoomDetails)} />
                    </>
                )}
            </Grid>
        );
    }
}


const mapStateToProps = (state) => {
    return {
        isTimelineVisible: bookRoomSelectors.isTimelineVisible(state),
        filters: bookRoomSelectors.getFilters(state),
        results: bookRoomSelectors.getSearchResults(state),
        suggestions: bookRoomSelectors.getSuggestions(state),
        totalResultCount: bookRoomSelectors.getTotalResultCount(state),
        isSearching: bookRoomSelectors.isSearching(state),
        hasConflicts: bookRoomSelectors.hasUnavailableRooms(state),
        roomDetailsFetching: roomsSelectors.isFetchingDetails(state),
        isInitializing: globalSelectors.isInitializing(state),
        queryString: stateToQueryString(state.bookRoom, qsFilterRules, qsBookRoomRules),
        showMap: globalSelectors.isMapVisible(state),
    };
};

const mapDispatchToProps = dispatch => ({
    searchRooms() {
        dispatch(bookRoomActions.searchRooms());
    },
    clearTextFilter() {
        dispatch(globalActions.setFilterParameter('bookRoom', 'text', null));
    },
    fetchRoomSuggestions() {
        dispatch(bookRoomActions.fetchRoomSuggestions());
    },
    resetRoomSuggestions() {
        dispatch(bookRoomActions.resetRoomSuggestions());
    },
    fetchRoomDetails(id) {
        dispatch(roomsActions.fetchDetails(id));
    },
    resetBookingAvailability() {
        dispatch(bookRoomActions.resetBookingAvailability());
    },
    setFilterParameter(param, value) {
        dispatch(globalActions.setFilterParameter('bookRoom', param, value));
    },
    toggleTimelineView(visible) {
        dispatch(bookRoomActions.toggleTimelineView(visible));
    },
    dispatch
});

export default connect(
    mapStateToProps,
    mapDispatchToProps,
    pushStateMergeProps
)(BookRoom);
