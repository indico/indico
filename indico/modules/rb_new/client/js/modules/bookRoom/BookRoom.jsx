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
import {bindActionCreators} from 'redux';
import _ from 'lodash';
import {Button, Card, Grid, Header, Icon, Label, Loader, Message, Popup, Sticky} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';

import {Overridable, Slot, toClasses} from 'indico/react/util';
import {PluralTranslate, Translate, Singular, Param, Plural} from 'indico/react/i18n';
import {serializeTime, toMoment} from 'indico/utils/date';
import searchBarFactory from '../../components/SearchBar';
import Room from '../../containers/Room';
import BookingFilterBar from './BookingFilterBar';
import {roomFilterBarFactory} from '../../modules/roomList';
import BookingTimeline from './BookingTimeline';
import SearchResultCount from './SearchResultCount';
import {TimelineHeader} from '../../common/timeline';
import {isDateWithinRange} from '../../util';
import {queryStringRules as qsFilterRules} from '../../common/roomSearch';
import {rules as qsBookRoomRules} from './queryString';
import * as bookRoomActions from './actions';
import {actions as filtersActions} from '../../common/filters';
import {actions as roomsActions} from '../../common/rooms';
import * as bookRoomSelectors from './selectors';
import {mapControllerFactory, selectors as mapSelectors} from '../../common/map';

import './BookRoom.module.scss';


const SearchBar = searchBarFactory('bookRoom', bookRoomSelectors);
const MapController = mapControllerFactory('bookRoom', bookRoomSelectors);
const RoomFilterBar = roomFilterBarFactory('bookRoom');

/* eslint-disable react/no-unused-state */
class BookRoom extends React.Component {
    static propTypes = {
        results: PropTypes.arrayOf(PropTypes.object).isRequired,
        isSearching: PropTypes.bool.isRequired,
        searchFinished: PropTypes.bool.isRequired,
        isTimelineVisible: PropTypes.bool.isRequired,
        hasConflicts: PropTypes.bool.isRequired,
        totalResultCount: PropTypes.number.isRequired,
        filters: PropTypes.object.isRequired,
        suggestions: PropTypes.arrayOf(PropTypes.object).isRequired,
        showMap: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            setFilterParameter: PropTypes.func.isRequired,
            clearTextFilter: PropTypes.func.isRequired,
            searchRooms: PropTypes.func.isRequired,
            fetchRoomSuggestions: PropTypes.func.isRequired,
            resetRoomSuggestions: PropTypes.func.isRequired,
            toggleTimelineView: PropTypes.func.isRequired,
            openRoomDetails: PropTypes.func.isRequired,
            openBookingForm: PropTypes.func.isRequired,
        }).isRequired,
        dateRange: PropTypes.array.isRequired,
        showSuggestions: PropTypes.bool
    };

    static defaultProps = {
        showSuggestions: true
    };

    state = {
        maxVisibleRooms: 20,
        suggestionsRequested: false,
    };

    static getDerivedStateFromProps({dateRange}, state) {
        if (!_.isEmpty(dateRange) && !isDateWithinRange(state.activeDate, dateRange, toMoment)) {
            return {...state, activeDate: toMoment(dateRange[0])};
        } else {
            return state;
        }
    }

    componentDidMount() {
        const {actions: {searchRooms}} = this.props;
        searchRooms();
    }

    componentDidUpdate({filters: prevFilters}) {
        const {filters} = this.props;
        if (!_.isEqual(prevFilters, filters)) {
            this.restartSearch();
        }
    }

    componentWillUnmount() {
        const {actions: {clearTextFilter}} = this.props;
        clearTextFilter();
    }

    restartSearch() {
        const {actions: {searchRooms, resetRoomSuggestions}} = this.props;
        searchRooms();
        resetRoomSuggestions();
        this.setState({maxVisibleRooms: 20, suggestionsRequested: false});
    }

    openBookingForm(room, overrides = null) {
        const {actions: {openBookingForm}, filters: {dates, timeSlot, recurrence}} = this.props;
        if (!overrides) {
            openBookingForm(room.id);
            return;
        }
        // if we have overrides, we need to pass the data explicitly
        const bookingData = {dates, timeSlot, recurrence};
        if (overrides.time) {
            const {startTime, endTime} = timeSlot;
            bookingData.timeSlot = {
                startTime: serializeTime(moment(startTime, 'HH:mm').add(overrides.time, 'minutes')),
                endTime: serializeTime(moment(endTime, 'HH:mm').add(overrides.time, 'minutes')),
            };
        } else if (overrides.duration) {
            const {startTime, endTime} = timeSlot;
            bookingData.timeSlot = {
                startTime,
                endTime: serializeTime(moment(endTime, 'HH:mm').subtract(overrides.duration, 'minutes'))
            };
        }
        openBookingForm(room.id, bookingData);
    }

    renderRoom = (room) => {
        const {actions: {openRoomDetails}} = this.props;
        const bookingModalBtn = (
            <Button positive icon="check" circular onClick={() => this.openBookingForm(room)} />
        );
        const showDetailsBtn = (
            <Button primary icon="search" circular onClick={() => openRoomDetails(room.id)} />
        );
        return (
            <Room key={room.id} room={room} showFavoriteButton>
                <Slot name="actions">
                    <Popup trigger={bookingModalBtn}
                           content={Translate.string('Book room')}
                           position="top center"
                           hideOnScroll />
                    <Popup trigger={showDetailsBtn}
                           content={Translate.string('Room details')}
                           position="top center"
                           hideOnScroll />
                </Slot>
            </Room>
        );
    };

    renderFilters(refName) {
        const {[refName]: ref, activeDate} = this.state;
        const {
            dateRange,
            isSearching,
            totalResultCount,
            results,
            isTimelineVisible
        } = this.props;

        const legendLabels = [
            {label: Translate.string('Available'), color: 'green'},
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Conflict'), color: 'red'},
            {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];
        return (
            <Sticky context={ref} className="sticky-filters">
                <div className="filter-row">
                    <div className="filter-row-filters">
                        <Overridable id="BookingFilterBar">
                            <BookingFilterBar />
                        </Overridable>
                        <RoomFilterBar />
                        <SearchBar />
                    </div>
                    {this.renderViewSwitch()}
                </div>
                <SearchResultCount matching={results.length}
                                   total={totalResultCount}
                                   isFetching={isSearching} />
                {isTimelineVisible && activeDate && (
                    <TimelineHeader activeDate={activeDate}
                                    onDateChange={(newDate) => {
                                        this.setState({
                                            activeDate: newDate
                                        });
                                    }}
                                    legendLabels={legendLabels}
                                    dateRange={dateRange} />
                )}
            </Sticky>
        );
    }

    hasMoreRooms = (allowSuggestions = true) => {
        const {maxVisibleRooms, suggestionsRequested} = this.state;
        const {results, searchFinished} = this.props;
        if (!searchFinished) {
            return false;
        }
        return maxVisibleRooms < results.length || (allowSuggestions && !suggestionsRequested);
    };

    loadMoreRooms = () => {
        const {actions: {fetchRoomSuggestions}, showSuggestions} = this.props;
        const {maxVisibleRooms} = this.state;
        if (this.hasMoreRooms(false)) {
            this.setState({maxVisibleRooms: maxVisibleRooms + 20});
        } else if (showSuggestions) {
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
            isSearching,
            isTimelineVisible,
            showSuggestions
        } = this.props;

        if (!isTimelineVisible) {
            return (
                <>
                    <div className="ui" styleName="available-room-list" ref={ref => this.handleContextRef(ref, 'tileRef')}>
                        {this.renderFilters('tileRef')}
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
                </>
            );
        } else {
            return (
                <div styleName="available-room-list" ref={(ref) => this.handleContextRef(ref, 'timelineRef')}>
                    {this.renderFilters('timelineRef')}
                    <BookingTimeline showSuggestions={showSuggestions} />
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

    renderSuggestionText = (room, {time, duration, skip}) => {
        return (
            <>
                {time && (
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.openBookingForm(room, {time})}
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
                {duration && (
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.openBookingForm(room, {duration})}
                             warning compact>
                        <Message.Header>
                            <Icon name="hourglass full" /> {PluralTranslate.string('One minute shorter', '{duration} minutes shorter', duration, {duration})}
                        </Message.Header>
                    </Message>
                )}
                {skip && (
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.openBookingForm(room)}
                             warning compact>
                        <Message.Header>
                            <Icon name="calendar times" /> {PluralTranslate.string('Skip one day', 'Skip {skip} days', skip, {skip})}
                        </Message.Header>
                    </Message>
                )}
            </>
        );
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
        const {actions: {toggleTimelineView}, isTimelineVisible} = this.props;
        if (isTimelineVisible) {
            toggleTimelineView(false);
            this.setState({timelineRef: null});
            this.restartSearch();
        }
    };

    switchToTimeline = () => {
        const {actions: {toggleTimelineView}, isTimelineVisible} = this.props;
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

    render() {
        const {showMap} = this.props;
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
        searchFinished: bookRoomSelectors.isSearchFinished(state),
        hasConflicts: bookRoomSelectors.hasUnavailableRooms(state),
        queryString: stateToQueryString(state.bookRoom, qsFilterRules, qsBookRoomRules),
        showMap: mapSelectors.isMapVisible(state),
        dateRange: bookRoomSelectors.getTimelineDateRange(state)
    };
};

const mapDispatchToProps = dispatch => ({
    actions: bindActionCreators({
        searchRooms: bookRoomActions.searchRooms,
        clearTextFilter: () => filtersActions.setFilterParameter('bookRoom', 'text', null),
        fetchRoomSuggestions: bookRoomActions.fetchRoomSuggestions,
        resetRoomSuggestions: bookRoomActions.resetRoomSuggestions,
        setFilterParameter: (param, value) => filtersActions.setFilterParameter('bookRoom', param, value),
        toggleTimelineView: bookRoomActions.toggleTimelineView,
        openRoomDetails: roomsActions.openRoomDetailsBook,
        openBookingForm: bookRoomActions.openBookingForm,
    }, dispatch),
});

export default connect(
    mapStateToProps,
    mapDispatchToProps,
)(BookRoom);
