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
import {Icon, Label, Menu, Message, Popup} from 'semantic-ui-react';
import {stateToQueryString} from 'redux-router-querystring/dist/routing';
import {Route, withRouter} from 'react-router-dom';
import {Translate, Param} from 'indico/react/i18n';
import {queryString as qsFilterRules} from '../../serializers/filters';
import {rules as qsBookRoomRules} from './queryString';

import './BookRoom.module.scss';
import * as selectors from './selectors';
import {pushStateMergeProps} from '../../util';
import UnavailableRoomsModal from './UnavailableRoomsModal';


class SearchResultCount extends React.Component {
    static propTypes = {
        isSearching: PropTypes.bool.isRequired,
        matching: PropTypes.number,
        total: PropTypes.number,
        pushState: PropTypes.func.isRequired
    };

    static defaultProps = {
        matching: null,
        total: null
    };

    renderRoomTotal(count) {
        const trigger = (
            <Menu.Item as="span">
                <Icon name="filter" />
                <Translate>
                    Total
                    <Param name="count"
                           value={<Label horizontal size="small">{count}</Label>} />
                </Translate>
            </Menu.Item>
        );
        return (
            <Popup trigger={trigger}>
                <Translate>
                    Number of rooms matching your filtering criteria.
                </Translate>
            </Popup>
        );
    }

    renderRoomAvailable(count) {
        const label = <Label color="teal" horizontal size="small">{count}</Label>;
        const trigger = (
            <Menu.Item active as="span">
                <Icon name="calendar alternate outline" />
                <Translate>
                    Available
                    <Param name="count"
                           value={label} />
                </Translate>
            </Menu.Item>
        );

        return (
            <Popup trigger={trigger}>
                <Translate>
                    Rooms that are free on that time slot.
                </Translate>
            </Popup>
        );
    }

    renderUnavailable(count) {
        const label = <Label color="red" horizontal size="small">{count}</Label>;
        const trigger = (
            <Menu.Item link onClick={this.openUnavailableRoomsModal}>
                <Icon name="remove" />
                <Translate>
                    Unavailable
                    <Param name="count"
                           value={label} />
                </Translate>
            </Menu.Item>
        );
        return (
            <Popup trigger={trigger}>
                <Translate>
                    Rooms unavailable during that time slot (click for details).
                </Translate>
            </Popup>
        );
    }

    renderNoRooms() {
        return (
            <Message icon="times circle outline"
                     error
                     content={Translate.string('No rooms match your query')} />
        );
    }

    renderNoMatching() {
        return (
            <Message icon="warning sign"
                     warning
                     content={Translate.string('No rooms are available during that timeslot')} />
        );
    }

    openUnavailableRoomsModal = () => {
        const {pushState} = this.props;
        pushState('/book/unavailable', true);
    };

    closeModal = () => {
        const {pushState} = this.props;
        pushState(`/book`, true);
    };

    render() {
        const {isSearching, matching, total} = this.props;
        const style = {
            display: (isSearching || (total > 0)) ? 'inline-flex' : 'none'
        };

        return (
            <div styleName="results-count">
                <Menu icon
                      styleName="results-count-menu"
                      className={isSearching ? 'loading' : null}
                      style={style}>
                    {isSearching ? (
                        <div styleName="loading-indicator">
                            <div className="bar" />
                            <div className="bar" />
                            <div className="bar" />
                        </div>
                    ) : (
                        !!total && (
                            <>
                                {this.renderRoomTotal(total)}
                                {this.renderRoomAvailable(matching)}
                                {(matching < total) && this.renderUnavailable(total - matching)}
                            </>
                        )
                    )}
                </Menu>
                {!isSearching && (
                    <>
                        {total > 0 && matching === 0 && this.renderNoMatching()}
                        {total === 0 && this.renderNoRooms()}
                    </>
                )}
                <Route exact path="/book/unavailable" render={() => (
                    <UnavailableRoomsModal onClose={this.closeModal} />
                )} />
            </div>
        );
    }
}

export default withRouter(connect(
    state => ({
        isSearching: selectors.isSearching(state),
        queryString: stateToQueryString(state.bookRoom, qsFilterRules, qsBookRoomRules)
    }),
    dispatch => ({
        dispatch
    }),
    pushStateMergeProps
)(SearchResultCount));
